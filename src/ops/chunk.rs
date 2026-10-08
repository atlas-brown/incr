use fastcdc::v2020::{self as cdc, MASKS, Normalization};

use crate::config::ChunkSizes;

pub(crate) struct ContentChunker {
    sizes: ChunkSizes,
    small_mask: u64,
    large_mask: u64,
    gear: Box<[u64; 256]>,
    hash: u64,
    length: usize,
    pending_boundary: bool,
}

impl ContentChunker {
    pub(crate) fn new(sizes: ChunkSizes) -> Self {
        assert!(sizes.minimum > 0 && sizes.minimum <= sizes.average);
        assert!(sizes.average <= sizes.maximum);
        let average = (sizes.average as f64).log2().round() as usize;
        let normalization = Normalization::Level1.bits() as usize;
        assert!(average >= normalization && average + normalization < MASKS.len());
        let (gear, _) = cdc::get_gear_with_seed(0);
        Self {
            sizes,
            small_mask: MASKS[average + normalization],
            large_mask: MASKS[average - normalization],
            gear,
            hash: 0,
            length: 0,
            pending_boundary: false,
        }
    }

    // Return the first boundary, independent of how the producer partitions writes.
    // Line-wise commands extend a content boundary through the next newline.
    pub(crate) fn next_boundary(&mut self, bytes: &[u8], align_lines: bool) -> Option<usize> {
        for (offset, &byte) in bytes.iter().enumerate() {
            self.length += 1;
            if self.length >= self.sizes.minimum && !self.pending_boundary {
                self.hash = (self.hash << 1).wrapping_add(self.gear[byte as usize]);
                let mask = if self.length < self.sizes.average {
                    self.small_mask
                } else {
                    self.large_mask
                };
                self.pending_boundary = self.hash & mask == 0 || self.length >= self.sizes.maximum;
            }
            if self.pending_boundary && (!align_lines || byte == b'\n') {
                self.hash = 0;
                self.length = 0;
                self.pending_boundary = false;
                return Some(offset + 1);
            }
        }
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use rand::rngs::StdRng;
    use rand::{Rng, SeedableRng};

    fn boundaries(bytes: &[u8], read_size: usize, align_lines: bool) -> Vec<usize> {
        let mut chunker = ContentChunker::new(ChunkSizes {
            minimum: 64,
            average: 256,
            maximum: 1024,
        });
        let mut boundaries = Vec::new();
        let mut consumed = 0;
        for read in bytes.chunks(read_size) {
            let mut remaining = read;
            while !remaining.is_empty() {
                match chunker.next_boundary(remaining, align_lines) {
                    Some(length) => {
                        consumed += length;
                        boundaries.push(consumed);
                        remaining = &remaining[length..];
                    }
                    None => {
                        consumed += remaining.len();
                        break;
                    }
                }
            }
        }
        boundaries
    }

    #[test]
    fn boundaries_do_not_depend_on_read_sizes() {
        let mut input = vec![0; 100_000];
        StdRng::seed_from_u64(53).fill(&mut input[..]);
        for align_lines in [false, true] {
            let expected = boundaries(&input, input.len(), align_lines);
            assert!(!expected.is_empty());
            for read_size in [1, 7, 64, 8192, 65536] {
                assert_eq!(expected, boundaries(&input, read_size, align_lines));
            }
            let mut previous = 0;
            for boundary in expected {
                assert!(boundary - previous >= 64);
                if align_lines {
                    assert_eq!(input[boundary - 1], b'\n');
                } else {
                    assert!(boundary - previous <= 1024);
                }
                previous = boundary;
            }
        }
    }

    #[test]
    fn repeated_bytes_still_have_bounded_chunks() {
        assert_eq!(boundaries(&[0; 4096], 17, false).last(), Some(&4096));
    }
}
