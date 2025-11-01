#!/bin/bash
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
BENCHMARK="image_annotation"
BENCHMARK_DIR="${TOP}/evaluation/benchmarks/${BENCHMARK}"
INPUT_DIR="${TOP}/evaluation/benchmarks/${BENCHMARK}/inputs"

URL="https://atlas.cs.brown.edu/data"
mkdir -p "$INPUT_DIR"
cd "$INPUT_DIR" || exit 1

mkdir -p "$INPUT_DIR"

size=full
for arg in "$@"; do
    case "$arg" in
    --small) size=small ;;
    --min) size=min ;;
    esac
done
export LC_ALL=C

if [[ "$size" == "small" ]]; then
    # if inputs exist
    if [[ -d "$INPUT_DIR/jpg.small" ]]; then
        echo "Image data already downloaded and extracted."
    else
        data_url="${URL}"/small/jpg.zip
        zip_dst=$INPUT_DIR/jpg.small.zip
        out_dir=$INPUT_DIR/jpg.small
        wget --no-check-certificate $data_url -O $zip_dst || {
            echo "Failed to download $data_url"
            exit 1
        }
        unzip $zip_dst -d $out_dir || {
            echo "Failed to unzip $zip_dst"
            exit 1
        }
        rm "$zip_dst"
    fi
    # if [[ -d "$INPUT_DIR/songs.small" ]]; then
    #     echo "Song already downloaded and extracted."
    #     exit 0
    # fi
    # data_url="${URL}/llm/playlist_small.tar.gz"
    # wget --no-check-certificate $data_url -O "$INPUT_DIR"/playlist_small.tar.gz || {
    #     echo "Failed to download $data_url"
    #     exit 1
    # }
    # tar -xzf "$INPUT_DIR/playlist_small.tar.gz" -C "$INPUT_DIR" || {
    #     echo "Failed to extract $INPUT_DIR/playlist_small.tar.gz"
    #     exit 1
    # }
    # rm "$INPUT_DIR/playlist_small.tar.gz"
    # mv "$INPUT_DIR/playlist_small" "$INPUT_DIR/songs.small"
    # exit 0

elif [[ "$size" == "min" ]]; then
    if [[ -d "$INPUT_DIR/jpg.min" ]]; then
        echo "Image data already downloaded and extracted."
    else
        cp -r "${BENCHMARK_DIR}"/min_inputs/jpg.min "$INPUT_DIR"
    fi
else
    if [[ -d "$INPUT_DIR/jpg" ]]; then
        echo "Image data already downloaded and extracted."
    else
        echo "Downloading full dataset."
        data_url=https://atlas-group.cs.brown.edu/data/full/jpg.zip
        zip_dst="$INPUT_DIR/jpg.zip"
        out_dir="$INPUT_DIR/jpg"
        wget --no-check-certificate $data_url -O $zip_dst
        unzip $zip_dst -d $out_dir
        rm "$zip_dst"
    fi
fi
