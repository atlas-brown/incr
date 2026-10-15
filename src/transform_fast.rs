//! Opt-in source-preserving compilation for a deliberately restricted shell CST.
//! Unsupported syntax or a failed capability/source check uses the Python path.
use clap::Parser;
use std::collections::{BTreeSet, HashSet};
use std::ffi::CString;
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Write};
use std::os::fd::FromRawFd;
use std::os::unix::fs::OpenOptionsExt;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::Instant;

const INSERT: &[u8] = include_bytes!("scripts/insert.py");
const SHELL_AST: &[u8] = include_bytes!("scripts/shell_ast.py");
const LIMIT: usize = 1024 * 1024;
const READY: &[u8] = b"incr-native-transform-v1\n";

#[derive(Parser)]
struct Arguments {
    #[arg(long)]
    sys_path: String,
    #[arg(long)]
    try_path: String,
    #[arg(long)]
    cache_path: String,
    #[arg(long)]
    observe_path: Option<String>,
    #[arg(long)]
    helper_source: PathBuf,
    #[arg(long)]
    ready: PathBuf,
    #[arg(long)]
    bash: bool,
    path: PathBuf,
}

pub(crate) fn entry() -> i32 {
    let args = std::iter::once(std::ffi::OsString::from("incr-transform")).chain(std::env::args_os().skip(2));
    let Ok(args) = Arguments::try_parse_from(args) else {
        return 3;
    };
    if perform(&args).is_some() { 0 } else { 3 }
}

fn perform(args: &Arguments) -> Option<()> {
    if args.bash
        || std::env::var_os("SHELLOPTS").is_some()
        || std::env::var_os("BASH_ENV").is_some_and(|v| !v.is_empty())
        || std::env::vars_os()
            .any(|(key, _)| key.to_string_lossy().starts_with("LD_") || key == "GLIBC_TUNABLES")
        || !matches_source(&args.helper_source, INSERT)?
        || !matches_source(&args.helper_source.parent()?.join("shell_ast.py"), SHELL_AST)?
    {
        return None;
    }
    let shell = std::env::var_os("INCR_SHELL").unwrap_or_else(|| "bash".into());
    let shell = executable(Path::new(&shell))?;
    if fs::canonicalize(shell).ok()? != fs::canonicalize("/bin/bash").ok()? {
        return None;
    }
    let mut source = Vec::new();
    let file = OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_NONBLOCK)
        .open(&args.path)
        .ok()?;
    if !file.metadata().ok()?.is_file() {
        return None;
    }
    file.take((LIMIT + 1) as u64).read_to_end(&mut source).ok()?;
    if source.len() > LIMIT {
        return None;
    }
    let text = std::str::from_utf8(&source).ok()?;
    let mut words = vec![
        args.sys_path.as_str(),
        "--try",
        args.try_path.as_str(),
        "--cache",
        args.cache_path.as_str(),
    ];
    if let Some(path) = &args.observe_path {
        words.extend(["--observe", path.as_str()]);
    }
    let prefix = shlex::try_join(words).ok()? + " ";
    let result = transform(text, &prefix)?;
    if !valid_bash(&args.path)? {
        return None;
    }
    if !matches_source(&args.path, &source)? {
        return None;
    }
    let mut ready = OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o600)
        .open(&args.ready)
        .ok()?;
    let mut output = std::io::stdout().lock();
    output.write_all(result.as_bytes()).ok()?;
    output.flush().ok()?;
    // A custom/older control binary cannot accidentally claim a successful
    // transformation just by printing arbitrary text and returning zero.
    ready.write_all(READY).ok()?;
    Some(())
}

fn matches_source(path: &Path, expected: &[u8]) -> Option<bool> {
    let file = OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_NONBLOCK)
        .open(path)
        .ok()?;
    if !file.metadata().ok()?.is_file() {
        return None;
    }
    let mut bytes = Vec::new();
    file.take((expected.len() + 1) as u64)
        .read_to_end(&mut bytes)
        .ok()?;
    Some(bytes == expected)
}

fn executable(name: &Path) -> Option<PathBuf> {
    let candidates = if name.components().count() > 1 || name.is_absolute() {
        vec![name.to_owned()]
    } else {
        std::env::split_paths(&std::env::var_os("PATH")?)
            .map(|p| p.join(name))
            .collect()
    };
    candidates.into_iter().find(|path| {
        let Ok(c) = CString::new(path.as_os_str().as_encoded_bytes()) else {
            return false;
        };
        path.is_file() && unsafe { libc::access(c.as_ptr(), libc::X_OK) } == 0
    })
}

fn valid_bash(path: &Path) -> Option<bool> {
    // Anonymous stderr avoids pipe-capacity deadlocks on long syntax diagnostics.
    let fd = unsafe { libc::memfd_create(c"incr-transform-check".as_ptr(), libc::MFD_CLOEXEC) };
    if fd < 0 {
        return None;
    }
    let error = unsafe { File::from_raw_fd(fd) };
    let status = Command::new("/usr/bin/timeout")
        .args(["--kill-after=1s", "5s", "/bin/bash", "-n", "--"])
        .arg(path)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(error.try_clone().ok()?)
        .status()
        .ok()?;
    Some(status.success() && error.metadata().ok()?.len() == 0)
}

fn transform(source: &str, prefix: &str) -> Option<String> {
    // Deliberately conservative: source introspection and dynamic bindings retain
    // the existing transformer. This initial path handles straightforward data
    // pipelines, assignments and redirections, not general Bash compilation.
    if source.contains('\0')
        || source.contains("|&")
        || [
            "LINENO", "BASH_", "FUNCNAME", "$0", "${0", "$@", "$*", "${@", "${*", "$'", "`",
        ]
        .iter()
        .any(|s| source.contains(s))
    {
        return None;
    }
    for rest in source.split("${").skip(1) {
        let name = rest.split('}').next()?;
        if name.is_empty()
            || !name.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'_')
            || name.as_bytes()[0].is_ascii_digit()
        {
            return None;
        }
    }
    let mut parser = tree_sitter::Parser::new();
    parser.set_language(&tree_sitter_bash::LANGUAGE.into()).ok()?;
    #[allow(deprecated)]
    parser.set_timeout_micros(500_000);
    let tree = parser.parse(source, None)?;
    if tree.root_node().has_error() {
        return None;
    }
    let ignored: HashSet<_> = std::str::from_utf8(INSERT)
        .ok()?
        .split("IGNORE_COMMANDS = [")
        .nth(1)?
        .split("]\nAVOID_SET")
        .next()?
        .lines()
        .filter_map(|line| line.trim().strip_prefix('"')?.split('"').next())
        .collect();
    let mut stack = vec![tree.root_node()];
    let mut positions = BTreeSet::new();
    let started = Instant::now();
    while let Some(node) = stack.pop() {
        if started.elapsed().as_millis() > 500 {
            return None;
        }
        if !matches!(
            node.kind(),
            "program"
                | "comment"
                | "command"
                | "command_name"
                | "word"
                | "variable_assignment"
                | "variable_name"
                | "string"
                | "raw_string"
                | "string_content"
                | "expansion"
                | "simple_expansion"
                | "concatenation"
                | "command_substitution"
                | "pipeline"
                | "redirected_statement"
                | "file_redirect"
                | "number"
                | "list"
                | "test_command"
                | "test_operator"
                | "unary_expression"
                | "binary_expression"
                | "regex"
        ) {
            return None;
        }
        let mut operators = node.walk();
        if node.children(&mut operators).any(|child| child.kind() == "&") {
            return None;
        }
        if node.kind() == "file_redirect" {
            let redirect = node.utf8_text(source.as_bytes()).ok()?;
            if redirect.contains(">&") || redirect.contains("<&") || redirect.starts_with("&>") {
                return None;
            }
        }
        if node.kind() == "command" {
            let name = node.child_by_field_name("name")?;
            let literal = name.utf8_text(source.as_bytes()).ok()?;
            if [
                "alias", "unalias", "eval", ".", "source", "enable", "export", "declare", "typeset", "local",
                "readonly", "hash", "set", "shopt", "trap", "exec", "builtin", "command", "history", "fc",
            ]
            .contains(&literal)
            {
                return None;
            }
            if !ignored.contains(literal) {
                if literal.is_empty()
                    || literal.starts_with('-')
                    || !literal
                        .bytes()
                        .all(|b| b.is_ascii_alphanumeric() || b"_./-".contains(&b))
                {
                    return None;
                }
                executable(Path::new(literal))?;
                positions.insert(name.start_byte());
            }
        }
        let mut cursor = node.walk();
        stack.extend(node.named_children(&mut cursor));
    }
    let length = source
        .len()
        .checked_add(positions.len().checked_mul(prefix.len())?)?;
    if length > 32 * LIMIT {
        return None;
    }
    let mut result = String::new();
    result.try_reserve_exact(length).ok()?;
    let mut previous = 0;
    for position in positions {
        result.push_str(&source[previous..position]);
        result.push_str(prefix);
        previous = position;
    }
    result.push_str(&source[previous..]);
    Some(result)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn benchmark_pipeline_subset_is_supported() {
        for source in [
            include_str!("../evaluation/benchmarks/covid/scripts/1.sh"),
            include_str!("../evaluation/benchmarks/weather/scripts/temp-analytics-1.sh"),
        ] {
            let mut parser = tree_sitter::Parser::new();
            parser.set_language(&tree_sitter_bash::LANGUAGE.into()).unwrap();
            let tree = parser.parse(source, None).unwrap();
            assert!(
                transform(source, "PREFIX ").is_some(),
                "{}",
                tree.root_node().to_sexp()
            );
        }
    }
    #[test]
    fn unsafe_or_ambiguous_constructs_fall_back() {
        for source in [
            "echo $LINENO",
            "f() { echo hi; }; f",
            "alias grep='echo'; grep x",
            "eval 'echo hi'",
            "cat <<EOF\nx\nEOF",
            "echo $(",
            "for x in a; do echo $x; done",
        ] {
            assert!(transform(source, "PREFIX ").is_none(), "accepted {source}");
        }
    }
    #[test]
    fn source_bytes_and_redirection_order_are_preserved() {
        let source = "# preserve comment\nx='a b'\n>result grep \"$x\" input | sort -n\n";
        let result = transform(source, "PREFIX ").expect("simple pipeline");
        assert_eq!(
            result,
            "# preserve comment\nx='a b'\n>result PREFIX grep \"$x\" input | PREFIX sort -n\n"
        );
    }
}
