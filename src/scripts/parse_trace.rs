use std::cell::RefCell;
use std::collections::HashMap;
use std::fs;
use std::path::{Component, Path, PathBuf};
use std::rc::Rc;

type Result<T> = std::result::Result<T, String>;

fn is_absolute(path: &str) -> bool {
    path.starts_with('/')
}
fn failed_syscall(result: &str) -> bool {
    result.trim_start().starts_with('-')
}

fn delimited_value<'path>(value: &'path str, open: &str, close: &str) -> Option<&'path str> {
    let start = value.find(open)? + open.len();
    let end = value.rfind(close)?;
    (end >= start).then(|| &value[start..end])
}

fn normalize_path<P: AsRef<Path>>(path: P) -> PathBuf {
    // Preserve parent components: resolving link/.. lexically can change its target.
    path.as_ref()
        .components()
        .filter(|component| *component != Component::CurDir)
        .collect()
}

/// Split arguments outside quoted strings and nested strace structures.
fn split_args(arguments: &str) -> Vec<String> {
    let mut output = Vec::new();
    let mut current_argument = String::new();
    let mut in_quotes = false;
    let mut angle_depth = 0usize; // depth for <>
    let mut square_depth = 0usize;
    let mut curly_depth = 0usize; // depth for {}
    let mut escaped = false;
    for character in arguments.chars() {
        if in_quotes && escaped {
            current_argument.push(character);
            escaped = false;
            continue;
        }
        if in_quotes && character == '\\' {
            current_argument.push(character);
            escaped = true;
            continue;
        }
        match character {
            '"' if angle_depth == 0 => {
                current_argument.push(character);
                in_quotes = !in_quotes;
            }
            '<' if !in_quotes => {
                angle_depth += 1;
                current_argument.push(character);
            }
            '>' if !in_quotes && angle_depth > 0 => {
                angle_depth -= 1;
                current_argument.push(character);
            }
            '{' if !in_quotes => {
                curly_depth += 1;
                current_argument.push(character);
            }
            '}' if !in_quotes && curly_depth > 0 => {
                curly_depth -= 1;
                current_argument.push(character);
            }
            '[' if !in_quotes => {
                square_depth += 1;
                current_argument.push(character);
            }
            ']' if !in_quotes && square_depth > 0 => {
                square_depth -= 1;
                current_argument.push(character);
            }
            ',' if !in_quotes && angle_depth == 0 && curly_depth == 0 && square_depth == 0 => {
                output.push(current_argument.trim().to_string());
                current_argument.clear();
            }
            _ => current_argument.push(character),
        }
    }
    if !current_argument.is_empty() {
        output.push(current_argument.trim().to_string());
    }
    output
}

/// Return the first argument and the remaining argument list.
fn take_first_arg(arguments: &str) -> (String, String) {
    let parts = split_args(arguments);
    if parts.is_empty() {
        return (String::new(), String::new());
    }
    let first = parts[0].clone();
    let rest = if parts.len() > 1 {
        parts[1..].join(",")
    } else {
        String::new()
    };
    (first, rest)
}

fn parse_string(value: &str) -> Result<String> {
    let value = value.trim();
    if value == "NULL" {
        return Ok(String::new());
    }
    let quoted = value
        .strip_prefix('"')
        .and_then(|value| value.strip_suffix('"'))
        .ok_or_else(|| format!("expected complete quoted string, got: {value}"))?;
    let mut decoded = Vec::with_capacity(quoted.len());
    let mut bytes = quoted.bytes().peekable();
    while let Some(byte) = bytes.next() {
        if byte != b'\\' {
            decoded.push(byte);
            continue;
        }
        let escape = bytes.next().ok_or("incomplete string escape")?;
        decoded.push(match escape {
            b'n' => b'\n',
            b'r' => b'\r',
            b't' => b'\t',
            b'b' => 8,
            b'f' => 12,
            b'v' => 11,
            b'a' => 7,
            b'"' => b'"',
            b'\\' => b'\\',
            b'0'..=b'7' => {
                let mut value = u16::from(escape - b'0');
                for _ in 0..2 {
                    if bytes.peek().is_some_and(|byte| matches!(byte, b'0'..=b'7')) {
                        value = value * 8 + u16::from(bytes.next().unwrap() - b'0');
                    } else {
                        break;
                    }
                }
                u8::try_from(value).map_err(|_| "invalid octal escape")?
            }
            b'x' => {
                let mut value = 0;
                for _ in 0..2 {
                    let digit = bytes
                        .next()
                        .and_then(|byte| char::from(byte).to_digit(16))
                        .ok_or("invalid hexadecimal escape")?;
                    value = value * 16 + digit as u8;
                }
                value
            }
            _ => return Err(format!("unsupported string escape: {}", char::from(escape))),
        });
    }
    String::from_utf8(decoded).map_err(|_| "non-UTF-8 trace path".to_owned())
}

fn returned_path(result: &str) -> Result<PathBuf> {
    if failed_syscall(result) {
        return Err("returned_path on error code".into());
    }
    let result = result.trim();
    let start = result.find('<').ok_or("no < in result")? + 1;
    let end = result.rfind('>').ok_or("no > in result")?;
    Ok(PathBuf::from(parse_string(&format!(
        "\"{}\"",
        &result[start..end]
    ))?))
}

fn absolute_path(directory: &Path, path: &str) -> PathBuf {
    normalize_path(if is_absolute(path) {
        PathBuf::from(path)
    } else {
        directory.join(path)
    })
}

#[derive(Clone, Debug, Eq, PartialEq)]
enum FileRecord {
    Read(PathBuf),
    Write(PathBuf),
}

impl FileRecord {
    fn with_parents(self) -> Vec<Self> {
        let path = match &self {
            Self::Read(path) | Self::Write(path) => path,
        };
        let mut records = vec![self.clone()];
        if path.is_absolute() {
            records.extend(
                path.ancestors()
                    .skip(1)
                    .map(|parent| Self::Read(parent.to_owned())),
            );
        }
        records
    }
}

struct Context {
    unfinished: HashMap<i32, String>,
    directories: HashMap<i32, Rc<RefCell<PathBuf>>>,
    initial_directory: PathBuf,
}

impl Context {
    fn new() -> Self {
        Self {
            unfinished: HashMap::new(),
            directories: HashMap::new(),
            initial_directory: std::env::current_dir().unwrap_or_else(|_| PathBuf::from("/")),
        }
    }

    fn clone_process(&mut self, parent: i32, child: i32, shared_directory: bool) {
        let directory = self.get_dir(parent);
        let directory = if shared_directory {
            Rc::clone(self.directories.get(&parent).unwrap())
        } else {
            Rc::new(RefCell::new(directory))
        };
        self.directories.insert(child, directory);
    }

    fn set_dir(&mut self, path: PathBuf, pid: i32) {
        self.get_dir(pid);
        *self.directories.get(&pid).unwrap().borrow_mut() = path;
    }

    fn get_dir(&mut self, pid: i32) -> PathBuf {
        self.directories
            .entry(pid)
            .or_insert_with(|| Rc::new(RefCell::new(self.initial_directory.clone())))
            .borrow()
            .clone()
    }

    fn push_half_line(&mut self, pid: i32, line: &str) {
        if let Some(offset) = line.find("<unfinished") {
            self.unfinished.insert(pid, line[..offset].trim().to_owned());
        }
    }

    fn pop_complete_line(&mut self, pid: i32, line: &str) -> Option<String> {
        let offset = line.find("resumed>")? + "resumed>".len();
        let prefix = self.unfinished.remove(&pid)?;
        Some(format!("{prefix}{}", line[offset..].trim()))
    }
}

fn reads_first_path(value: &str) -> bool {
    matches!(
        value,
        "execve"
            | "stat"
            | "lstat"
            | "access"
            | "statfs"
            | "readlink"
            | "getxattr"
            | "lgetxattr"
            | "llistxattr"
    )
}
fn writes_first_path(value: &str) -> bool {
    matches!(
        value,
        "mkdir"
            | "rmdir"
            | "truncate"
            | "creat"
            | "chmod"
            | "chown"
            | "lchown"
            | "utime"
            | "mknod"
            | "utimes"
            | "acct"
            | "unlink"
            | "setxattr"
            | "removexattr"
    )
}
fn reads_descriptor_path(value: &str) -> bool {
    matches!(
        value,
        "fstatat"
            | "newfstatat"
            | "statx"
            | "name_to_handle_at"
            | "readlinkat"
            | "faccessat"
            | "execveat"
            | "faccessat2"
    )
}
fn writes_descriptor_path(value: &str) -> bool {
    matches!(
        value,
        "unlinkat" | "utimensat" | "mkdirat" | "mknodat" | "fchownat" | "futimeat" | "fchmodat" | "fchmodat2"
    )
}
fn strip_pid(line: &str) -> Result<(i32, &str)> {
    let line = line.trim();
    let (process_id, rest) = line.split_once(' ').ok_or("expect pid")?;
    let pid = process_id.parse::<i32>().map_err(|_| "expect pid".to_string())?;
    Ok((pid, rest))
}

fn first_path(pid: i32, arguments: &str, context: &mut Context) -> Result<PathBuf> {
    let first = split_args(arguments).first().cloned().ok_or("no arg")?;
    let path = parse_string(&first)?;
    Ok(absolute_path(&context.get_dir(pid), &path))
}

fn write_first_path(pid: i32, arguments: &str, result: &str, context: &mut Context) -> Result<FileRecord> {
    let path = first_path(pid, arguments, context)?;
    Ok(if failed_syscall(result) {
        FileRecord::Read(path)
    } else {
        FileRecord::Write(path)
    })
}

fn path_arguments(
    pid: i32,
    positions: &[usize],
    arguments: &str,
    context: &mut Context,
) -> Result<Vec<PathBuf>> {
    let parts = split_args(arguments);
    let mut output = Vec::new();
    for &position in positions {
        let argument = parts.get(position).ok_or("missing path argument")?;
        let value = parse_string(argument)?;
        output.push(absolute_path(&context.get_dir(pid), &value));
    }
    Ok(output)
}

fn parse_rename(pid: i32, arguments: &str, result: &str, context: &mut Context) -> Result<Vec<FileRecord>> {
    Ok(path_arguments(pid, &[0, 1], arguments, context)?
        .into_iter()
        .map(|path| {
            if failed_syscall(result) {
                FileRecord::Read(path)
            } else {
                FileRecord::Write(path)
            }
        })
        .collect())
}

fn parse_link(pid: i32, arguments: &str, result: &str, context: &mut Context) -> Result<Vec<FileRecord>> {
    let paths = path_arguments(pid, &[0, 1], arguments, context)?;
    Ok(vec![
        FileRecord::Read(paths[0].clone()),
        if failed_syscall(result) {
            FileRecord::Read(paths[1].clone())
        } else {
            FileRecord::Write(paths[1].clone())
        },
    ])
}

fn parse_chdir(pid: i32, arguments: &str, result: &str, context: &mut Context) -> Result<PathBuf> {
    let new_path = first_path(pid, arguments, context)?;
    if !failed_syscall(result) {
        context.set_dir(new_path.clone(), pid);
    }
    Ok(normalize_path(new_path))
}

fn handle_open_common(path: PathBuf, flags: &str, result: &str) -> Result<Vec<FileRecord>> {
    if failed_syscall(result) {
        return Ok(vec![FileRecord::Read(path)]);
    }
    let written = ["O_WRONLY", "O_RDWR", "O_TRUNC", "O_CREAT", "O_TMPFILE"]
        .iter()
        .any(|flag| flags.contains(flag));
    Ok([path, returned_path(result)?]
        .into_iter()
        .map(|path| {
            if written {
                FileRecord::Write(path)
            } else {
                FileRecord::Read(path)
            }
        })
        .collect())
}

fn parse_openat(pid: i32, arguments: &str, result: &str, context: &mut Context) -> Result<Vec<FileRecord>> {
    let parts = split_args(arguments);
    if parts.len() < 3 {
        return Err("incomplete openat arguments".to_owned());
    }
    let total_path = descriptor_path(pid, arguments, context)?;
    let flags = parts.get(2).map(String::as_str).unwrap_or("");
    handle_open_common(total_path, flags, result)
}

fn parse_open(pid: i32, arguments: &str, result: &str, context: &mut Context) -> Result<Vec<FileRecord>> {
    let total_path = first_path(pid, arguments, context)?;
    let parts = split_args(arguments);
    let flags = parts.get(1).map(String::as_str).unwrap_or("");
    handle_open_common(total_path, flags, result)
}

fn descriptor_path(pid: i32, arguments: &str, context: &mut Context) -> Result<PathBuf> {
    let parts = split_args(arguments);
    let descriptor = parts.first().cloned().unwrap_or_default();
    let quoted_path = parts.get(1).cloned().unwrap_or_default();
    let path = parse_string(&quoted_path)?;
    if !path.is_empty() && is_absolute(&path) {
        return Ok(normalize_path(path));
    }
    let base = match delimited_value(&descriptor, "<", ">") {
        Some(path) => PathBuf::from(parse_string(&format!("\"{path}\""))?),
        None if descriptor == "AT_FDCWD" => context.get_dir(pid),
        None => return Err(format!("unresolved directory descriptor: {descriptor}")),
    };
    Ok(normalize_path(base.join(path)))
}

fn parse_renameat(pid: i32, arguments: &str, result: &str, context: &mut Context) -> Result<Vec<FileRecord>> {
    let path_a = descriptor_path(pid, arguments, context)?;
    let rest = split_args(arguments)
        .into_iter()
        .skip(2)
        .collect::<Vec<_>>()
        .join(",");
    let path_b = descriptor_path(pid, &rest, context)?;
    Ok(if failed_syscall(result) {
        vec![FileRecord::Read(path_a), FileRecord::Read(path_b)]
    } else {
        vec![FileRecord::Write(path_a), FileRecord::Write(path_b)]
    })
}

fn write_descriptor_path(
    pid: i32,
    arguments: &str,
    result: &str,
    context: &mut Context,
) -> Result<FileRecord> {
    let path = descriptor_path(pid, arguments, context)?;
    Ok(if failed_syscall(result) {
        FileRecord::Read(path)
    } else {
        FileRecord::Write(path)
    })
}

fn parse_clone(pid: i32, arguments: &str, result: &str, context: &mut Context) {
    if let Ok(child) = result.trim().parse::<i32>()
        && child > 0
    {
        let shared_directory = arguments
            .split(|character: char| !character.is_ascii_alphanumeric() && character != '_')
            .any(|flag| flag == "CLONE_FS");
        context.clone_process(pid, child, shared_directory);
    }
}

fn parse_symlinkat(pid: i32, arguments: &str, result: &str, context: &mut Context) -> Result<FileRecord> {
    let (_, rest) = take_first_arg(arguments);
    write_descriptor_path(pid, &rest, result, context)
}
fn parse_symlink(pid: i32, arguments: &str, result: &str, context: &mut Context) -> Result<FileRecord> {
    let (_, rest) = take_first_arg(arguments);
    write_first_path(pid, &rest, result, context)
}
fn parse_inotify_add_watch(pid: i32, arguments: &str, context: &mut Context) -> Result<PathBuf> {
    let (_fd, rest) = take_first_arg(arguments);
    first_path(pid, &rest, context)
}

fn parse_syscall(
    pid: i32,
    syscall: &str,
    arguments: &str,
    result: &str,
    context: &mut Context,
) -> Result<Vec<FileRecord>> {
    if reads_first_path(syscall) {
        return Ok(vec![FileRecord::Read(first_path(pid, arguments, context)?)]);
    }
    if writes_first_path(syscall) {
        return Ok(vec![write_first_path(pid, arguments, result, context)?]);
    }

    match syscall {
        "openat" | "openat2" => parse_openat(pid, arguments, result, context),
        "chdir" => Ok(vec![FileRecord::Read(parse_chdir(
            pid, arguments, result, context,
        )?)]),
        "open" => parse_open(pid, arguments, result, context),
        value if reads_descriptor_path(value) => {
            Ok(vec![FileRecord::Read(descriptor_path(pid, arguments, context)?)])
        }
        value if writes_descriptor_path(value) => {
            Ok(vec![write_descriptor_path(pid, arguments, result, context)?])
        }
        "rename" => parse_rename(pid, arguments, result, context),
        "renameat" | "renameat2" => parse_renameat(pid, arguments, result, context),
        "symlinkat" => Ok(vec![parse_symlinkat(pid, arguments, result, context)?]),
        "linkat" => {
            let source = descriptor_path(pid, arguments, context)?;
            let destination_arguments = split_args(arguments)
                .into_iter()
                .skip(2)
                .collect::<Vec<_>>()
                .join(",");
            Ok(vec![
                FileRecord::Read(source),
                write_descriptor_path(pid, &destination_arguments, result, context)?,
            ])
        }
        "link" => parse_link(pid, arguments, result, context),
        "symlink" => Ok(vec![parse_symlink(pid, arguments, result, context)?]),
        "clone" | "clone3" | "fork" | "vfork" => {
            parse_clone(pid, arguments, result, context);
            Ok(vec![])
        }
        "inotify_add_watch" => Ok(vec![FileRecord::Read(parse_inotify_add_watch(
            pid, arguments, context,
        )?)]),
        "getpid" | "getcwd" => Ok(vec![]),
        _ => Err(format!("unsupported syscall: {syscall}")),
    }
}

fn syscall_fields(line: &str) -> Result<(&str, &str, &str)> {
    let opening = line.find('(').ok_or("missing syscall arguments")?;
    let mut quoted = false;
    let mut escaped = false;
    let mut angle_depth = 0usize;
    let mut parentheses = 1usize;
    for (offset, byte) in line.bytes().enumerate().skip(opening + 1) {
        if quoted && escaped {
            escaped = false;
            continue;
        }
        if quoted && byte == b'\\' {
            escaped = true;
            continue;
        }
        if byte == b'"' && angle_depth == 0 {
            quoted = !quoted;
            continue;
        }
        if quoted {
            continue;
        }
        match byte {
            b'<' => angle_depth += 1,
            b'>' => angle_depth = angle_depth.saturating_sub(1),
            b'(' if angle_depth == 0 => parentheses += 1,
            b')' if angle_depth == 0 => {
                parentheses -= 1;
                if parentheses == 0 {
                    let result = line[offset + 1..]
                        .trim_start()
                        .strip_prefix('=')
                        .ok_or("missing syscall result")?;
                    return Ok((&line[..opening], &line[opening + 1..offset], result.trim()));
                }
            }
            _ => {}
        }
    }
    Err("incomplete syscall record".to_owned())
}

fn parse_line(line: &str, context: &mut Context) -> Result<Option<Vec<FileRecord>>> {
    let trimmed = line.trim();
    if trimmed.is_empty() {
        return Ok(Some(vec![]));
    }
    let (pid, rest) = strip_pid(trimmed)?;
    if rest.ends_with("+++") || rest.ends_with("---") {
        return Ok(None);
    }

    let mut line = rest.to_string();
    if line.ends_with("<unfinished ...>") {
        context.push_half_line(pid, &line);
        return Ok(Some(vec![]));
    } else if line.starts_with("<... ") {
        line = context
            .pop_complete_line(pid, &line)
            .ok_or("resumed syscall without entry")?;
    }
    line = line.trim().to_owned();

    let (syscall, arguments, result) = syscall_fields(&line)?;

    parse_syscall(pid, syscall, arguments, result, context).map(Some)
}

fn gather_dependencies(lines: &str, context: &mut Context) -> crate::execution::Trace {
    let mut trace = crate::execution::Trace::default();
    for line in lines.lines() {
        let records = match parse_line(line, context) {
            Ok(Some(records)) => records,
            Ok(None) => continue,
            Err(reason) => {
                trace.replay_barriers.push(reason);
                continue;
            }
        };
        for record in records {
            let path = match &record {
                FileRecord::Read(path) | FileRecord::Write(path) => path,
            };
            if path.starts_with("/dev") || path.starts_with("/tmp/pash_spec") {
                continue;
            }
            for record in record.with_parents() {
                match record {
                    FileRecord::Read(path) => {
                        trace.reads.insert(path);
                    }
                    FileRecord::Write(path) => {
                        trace.writes.insert(path);
                    }
                }
            }
        }
    }
    trace.reads.extend(trace.writes.iter().cloned());
    if !context.unfinished.is_empty() {
        trace.replay_barriers.push("unfinished syscalls".to_owned());
    }
    trace.replay_barriers.sort();
    trace.replay_barriers.dedup();
    trace
}

pub(crate) fn parse_trace(trace_path: &Path) -> anyhow::Result<crate::execution::Trace> {
    let data = fs::read_to_string(trace_path)?;
    Ok(gather_dependencies(&data, &mut Context::new()))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn parse(lines: &str) -> crate::execution::Trace {
        let mut context = Context::new();
        context.initial_directory = PathBuf::from("/start");
        gather_dependencies(lines, &mut context)
    }

    #[test]
    fn strings_preserve_utf8_and_c_escapes() {
        for spelling in [r#""café""#, r#""caf\303\251""#, r#""caf\xc3\xa9""#] {
            assert_eq!(parse_string(spelling).unwrap(), "café");
        }
        assert_eq!(parse_string(r#""a\",b\\c\n""#).unwrap(), "a\",b\\c\n");
        assert!(parse_string(r#""truncated"..."#).is_err());
        assert!(parse_string(r#""\377""#).is_err());
    }

    #[test]
    fn quoted_commas_arrays_and_structures_stay_in_their_arguments() {
        let arguments = split_args(r#""a\",b", [1, 2], {flags=O_RDONLY, mode=0}"#);
        assert_eq!(arguments, [r#""a\",b""#, "[1, 2]", "{flags=O_RDONLY, mode=0}"]);
        let trace = parse(r#"1 openat(AT_FDCWD, "a\",b", O_RDONLY) = 3</start/a",b>"#);
        assert!(trace.replay_barriers.is_empty(), "{:?}", trace.replay_barriers);
        assert!(trace.reads.contains(Path::new("/start/a\",b")));
    }

    #[test]
    fn returned_paths_can_contain_syscall_delimiters() {
        let trace = parse(r#"1 openat(AT_FDCWD, "file)=name", O_RDONLY) = 3</start/file)=name>"#);
        assert!(trace.replay_barriers.is_empty());
        assert!(trace.reads.contains(Path::new("/start/file)=name")));
    }

    #[test]
    fn forked_directories_are_copied_and_clone_fs_directories_are_shared() {
        let trace = parse(
            r#"1 chdir("/parent") = 0
1 clone(flags=SIGCHLD) = 2
2 chdir("child") = 0
1 stat("parent-file", {}) = 0
2 clone(flags=CLONE_FS|SIGCHLD) = 3
3 clone(flags=CLONE_FS|SIGCHLD) = 4
4 chdir("shared") = 0
2 newfstatat(AT_FDCWD, "child-file", {}, 0) = 0
3 newfstatat(AT_FDCWD, "peer-file", {}, 0) = 0"#,
        );
        assert!(trace.replay_barriers.is_empty(), "{:?}", trace.replay_barriers);
        for path in [
            "/parent/parent-file",
            "/parent/child/shared/child-file",
            "/parent/child/shared/peer-file",
        ] {
            assert!(trace.reads.contains(Path::new(path)), "{path}");
        }
    }

    #[test]
    fn failed_renames_are_reads_and_links_track_both_paths() {
        let trace = parse(
            r#"1 rename("missing", "destination") = -1 ENOENT (No such file or directory)
1 link("source", "alias") = 0
1 linkat(AT_FDCWD, "source", AT_FDCWD, "other-alias", 0) = 0"#,
        );
        assert!(trace.replay_barriers.is_empty());
        assert_eq!(
            trace.writes,
            [PathBuf::from("/start/alias"), PathBuf::from("/start/other-alias")].into()
        );
        for path in ["/start/missing", "/start/destination", "/start/source"] {
            assert!(trace.reads.contains(Path::new(path)), "{path}");
        }
    }

    #[test]
    fn readonly_create_is_a_write_and_parent_components_are_preserved() {
        let trace = parse(
            r#"1 openat(AT_FDCWD, "created", O_RDONLY|O_CREAT, 0666) = 3</start/created>
1 newfstatat(AT_FDCWD, "link/../input", {}, 0) = 0"#,
        );
        assert!(trace.replay_barriers.is_empty());
        assert!(trace.writes.contains(Path::new("/start/created")));
        assert!(trace.reads.contains(Path::new("/start/link/../input")));
    }

    #[test]
    fn unfinished_calls_resume_and_incomplete_records_block_reuse() {
        let trace = parse(
            r#"1 openat(AT_FDCWD, "input", O_RDONLY <unfinished ...>
1 <... openat resumed>) = 3</start/input>"#,
        );
        assert!(trace.replay_barriers.is_empty());
        assert!(trace.reads.contains(Path::new("/start/input")));
        for line in [
            r#"1 openat(AT_FDCWD, "input", O_RDONLY <unfinished ...>"#,
            r#"1 openat(AT_FDCWD, "truncated"..., O_RDONLY) = -1 ENOENT"#,
            "1 unknown_file_operation(1) = 0",
        ] {
            assert!(!parse(line).replay_barriers.is_empty(), "{line}");
        }
    }
}
