use anyhow::Result;
use fastcdc::v2020::{
    self as cdc, AVERAGE_MAX, AVERAGE_MIN, MASKS, MAXIMUM_MAX, MAXIMUM_MIN, MINIMUM_MAX, MINIMUM_MIN,
    Normalization,
};
use std::io::{ErrorKind, Read};

use crate::config::{BUFFER_SIZE, ChunkSizes};

#[derive(Clone, Debug)]
pub(crate) struct LineReader<R>
where
    R: Read,
{
    stream: R,
    group_size: usize,
    stream_closed: bool,

    chunk: Box<[u8; BUFFER_SIZE]>,
    data: Vec<u8>,
    start_index: usize,
    current_index: usize,
    current_lines: usize,
}

impl<R> LineReader<R>
where
    R: Read,
{
    pub(crate) fn new(stream: R, group_size: usize) -> Self {
        assert!(group_size > 0);
        Self {
            stream,
            group_size,
            stream_closed: false,

            chunk: vec![0; BUFFER_SIZE].into_boxed_slice().try_into().unwrap(),
            data: Vec::new(),
            start_index: 0,
            current_index: 0,
            current_lines: 0,
        }
    }

    pub(crate) fn read(&mut self) -> Result<bool> {
        if self.stream_closed {
            return Ok(true);
        }
        let count = loop {
            match self.stream.read(self.chunk.as_mut_slice()) {
                Ok(0) => {
                    self.stream_closed = true;
                    return Ok(true);
                }
                Ok(count) => break count,
                Err(error) if error.kind() == ErrorKind::Interrupted => continue,
                Err(error) => return Err(error.into()),
            }
        };
        self.data.extend_from_slice(&self.chunk[..count]);
        Ok(false)
    }

    pub(crate) fn next_lines(&mut self) -> Option<&[u8]> {
        debug_assert!(self.start_index <= self.current_index);
        debug_assert!(self.current_lines < self.group_size);

        while self.current_index < self.data.len() && self.current_lines < self.group_size {
            if self.data[self.current_index] == b'\n' {
                self.current_lines += 1;
            }
            self.current_index += 1;
        }

        if self.current_lines == self.group_size || (self.stream_closed && self.start_index < self.data.len())
        {
            let lines = &self.data[self.start_index..self.current_index];
            self.start_index = self.current_index;
            self.current_lines = 0;
            Some(lines)
        } else {
            None
        }
    }

    pub(crate) fn drain(&mut self) {
        self.data.drain(..self.start_index);
        self.current_index -= self.start_index;
        self.start_index = 0;
    }
}

pub(crate) struct LineChunker {
    sizes: ChunkSizes,
    mask_s: u64,
    mask_l: u64,
    mask_s_ls: u64,
    mask_l_ls: u64,
    gear: Box<[u64; 256]>,
    gear_ls: Box<[u64; 256]>,

    hash: u64,
    length: usize,
    start_time: std::time::Instant,
}

impl LineChunker {
    pub(crate) fn new(sizes: ChunkSizes) -> Self {
        assert!(MINIMUM_MIN as usize <= sizes.minimum && sizes.minimum <= MINIMUM_MAX as usize);
        assert!(AVERAGE_MIN as usize <= sizes.average && sizes.average <= AVERAGE_MAX as usize);
        assert!(MAXIMUM_MIN as usize <= sizes.maximum && sizes.maximum <= MAXIMUM_MAX as usize);

        let average = (sizes.average as f64).log2().round() as u32;
        let normalization = Normalization::Level1.bits();
        let mask_s = MASKS[(average + normalization) as usize];
        let mask_l = MASKS[(average - normalization) as usize];
        let (gear, gear_ls) = cdc::get_gear_with_seed(0);

        Self {
            sizes,
            mask_s,
            mask_l,
            mask_s_ls: mask_s << 1,
            mask_l_ls: mask_l << 1,
            gear,
            gear_ls,

            hash: 0,
            length: 0,
            start_time: std::time::Instant::now(),
        }
    }

    pub(crate) fn update(&mut self, lines: &[u8]) -> bool {
        let mut boundary = false;
        for &byte in lines {
            let length_before = self.length;
            if self.update_hash(byte) {
                //eprintln!("new chunk: {length_before} {:?}", self.start_time.elapsed());
                self.start_time = std::time::Instant::now();
                boundary = true;
            }
        }
        boundary
    }

    fn update_hash(&mut self, byte: u8) -> bool {
        let mut boundary = false;
        if self.length >= self.sizes.maximum {
            self.hash = 0;
            self.length = 0;
            boundary = true;
        }

        self.length += 1;
        let min_length = (self.sizes.minimum / 2) * 2;
        if self.length <= min_length {
            return boundary;
        }

        let index = self.length - 1;
        let offset = index - min_length;
        let gear_ls = offset % 2 == 0;
        let small = index < self.sizes.average;

        if gear_ls {
            self.hash = (self.hash << 2).wrapping_add(self.gear_ls[byte as usize]);
            let mask = if small { self.mask_s_ls } else { self.mask_l_ls };
            if (self.hash & mask) == 0 {
                self.hash = 0;
                self.length = 1;
                return true;
            }
        } else {
            self.hash = self.hash.wrapping_add(self.gear[byte as usize]);
            let mask = if small { self.mask_s } else { self.mask_l };
            if (self.hash & mask) == 0 {
                self.hash = 0;
                self.length = 1;
                return true;
            }
        }

        boundary
    }
}

#[allow(unused)]
#[derive(Clone, Debug)]
pub(crate) struct ReferenceLineChunker {
    sizes: ChunkSizes,
    mask_s: u64,
    mask_l: u64,
    mask_s_ls: u64,
    mask_l_ls: u64,
    data: Vec<u8>,
}

impl ReferenceLineChunker {
    #[allow(unused)]
    pub(crate) fn new(sizes: ChunkSizes) -> Self {
        assert!(MINIMUM_MIN as usize <= sizes.minimum && sizes.minimum <= MINIMUM_MAX as usize);
        assert!(AVERAGE_MIN as usize <= sizes.average && sizes.average <= AVERAGE_MAX as usize);
        assert!(MAXIMUM_MIN as usize <= sizes.maximum && sizes.maximum <= MAXIMUM_MAX as usize);

        let average = (sizes.average as f64).log2().round() as u32;
        let normalization = Normalization::Level1.bits();
        let mask_s = MASKS[(average + normalization) as usize];
        let mask_l = MASKS[(average - normalization) as usize];

        Self {
            sizes,
            mask_s,
            mask_l,
            mask_s_ls: mask_s << 1,
            mask_l_ls: mask_l << 1,
            data: Vec::new(),
        }
    }

    #[allow(unused)]
    pub(crate) fn update(&mut self, lines: &[u8]) -> bool {
        self.data.extend_from_slice(lines);
        let (_, count) = cdc::cut(
            &self.data,
            self.sizes.minimum,
            self.sizes.average,
            self.sizes.maximum,
            self.mask_s,
            self.mask_l,
            self.mask_s_ls,
            self.mask_l_ls,
        );
        if 0 < count && count < self.data.len() {
            self.data.drain(..count);
            true
        } else {
            false
        }
    }
}

#[cfg(test)]
mod test {
    use rand::rngs::StdRng;
    use rand::{Rng, SeedableRng};

    use crate::config::ChunkSizes;
    use crate::ops::chunk::{LineChunker, ReferenceLineChunker};

    const CHUNK_SIZES: ChunkSizes = ChunkSizes {
        minimum: 64,
        average: 256,
        maximum: 1024,
    };
    const LINES_SIZE: usize = 64;
    const TEST_CHUNKS: usize = 10_000;

    #[test]
    fn compare_chunkers() {
        let mut rng = StdRng::seed_from_u64(0);
        let mut chunker = LineChunker::new(CHUNK_SIZES);
        let mut reference_chunker = ReferenceLineChunker::new(CHUNK_SIZES);
        let mut lines = [0; LINES_SIZE];

        let min_chunks = (CHUNK_SIZES.maximum * TEST_CHUNKS) / LINES_SIZE;
        let mut num_chunks = 0;
        let mut differences = 0;
        for _ in 0..min_chunks {
            rng.fill(&mut lines);
            let boundary = chunker.update(&lines);
            let reference_boundary = reference_chunker.update(&lines);
            if boundary {
                num_chunks += 1;
            }
            if boundary != reference_boundary {
                differences += 1;
            }
        }

        assert!(differences < num_chunks / 50);
    }
}
