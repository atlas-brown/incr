#!/bin/bash
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
BENCHMARK="dpt"
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

URL='https://atlas.cs.brown.edu/data'

full_dir="${INPUT_DIR}/dpt.full"
small_dir="${INPUT_DIR}/dpt.small"
min_dir="${INPUT_DIR}/dpt.min"
models_dir="${INPUT_DIR}/models"

if [ ! -d "$models_dir" ]; then
    mkdir -p "$models_dir"
    wget --no-check-certificate "${URL}/models.zip" -O "${INPUT_DIR}/models.zip"
    unzip -q "${INPUT_DIR}/models.zip" -d "${INPUT_DIR}/tmp_models"
    mv "${INPUT_DIR}/tmp_models"/models/* "$models_dir"
    rm -r "${INPUT_DIR}/tmp_models" "${INPUT_DIR}/models.zip"
fi

if [[ "$size" == "min" ]]; then
    if ! ls "$min_dir/dpt.ref"/*.jpg &>/dev/null 2>&1; then
        mkdir -p "$min_dir/dpt.ref"
        ls "${BENCHMARK_DIR}/min_inputs/jpg.min/jpg/"*.jpg | sort | head -1 | \
            xargs -I{} cp {} "$min_dir/dpt.ref/"
        echo "Min reference images prepared ($(ls "$min_dir/dpt.ref/"*.jpg | wc -l) images)."
    fi
    mkdir -p "$min_dir/dpt"
    cp "$min_dir/dpt.ref/"*.jpg "$min_dir/dpt/"
    echo "Min working images ready ($(ls "$min_dir/dpt/"*.jpg | wc -l) images)."
fi

if [[ "$size" == "small" ]]; then
    if ls "$small_dir/dpt"/*.jpg &>/dev/null 2>&1; then
        echo "Small image data already prepared."
    else
        mkdir -p "$small_dir/dpt"
        tmpdir=$(mktemp -d)
        wget --no-check-certificate "https://atlas-group.cs.brown.edu/data/dpt/dpt.zip" \
            -O "$tmpdir/dpt.zip"
        unzip -q "$tmpdir/dpt.zip" -d "$tmpdir/dpt"
        find "$tmpdir/dpt" -name "*.jpg" | sort | head -10 | \
            xargs -I{} cp {} "$small_dir/dpt/"
        rm -rf "$tmpdir"
        echo "Small images prepared ($(ls "$small_dir/dpt/"*.jpg | wc -l) images)."
    fi
fi

# if [[ "$size" == "full" ]]; then
#     if [ -d "$full_dir" ]; then
#         echo "Data already downloaded and extracted."
#     else
#         mkdir -p "$full_dir"
#         wget --no-check-certificate "${URL}/pl-01-PFW-20250401T083800Z-001.zip" -O "${INPUT_DIR}/full.zip"
#         unzip -q "${INPUT_DIR}/full.zip" -d "${INPUT_DIR}/tmp_full"
#         mv "${INPUT_DIR}/tmp_full"/*/* "$full_dir"
#         rm -r "${INPUT_DIR}/tmp_full" "${INPUT_DIR}/full.zip"
#     fi
# fi

# URL="https://atlas-group.cs.brown.edu/data"

# if [[ "$size" == "small" ]]; then
#     # if inputs exist
#     if [[ -d "$INPUT_DIR/jpg.small" ]]; then
#         echo "Image data already downloaded and extracted."
#     else
#         data_url="${URL}"/small/jpg.zip
#         zip_dst=$INPUT_DIR/jpg.small.zip
#         out_dir=$INPUT_DIR/jpg.small
#         wget --no-check-certificate $data_url -O $zip_dst || {
#             echo "Failed to download $data_url"
#             exit 1
#         }
#         unzip $zip_dst -d $out_dir || {
#             echo "Failed to unzip $zip_dst"
#             exit 1
#         }
#         rm "$zip_dst"
#     fi
#     # if [[ -d "$INPUT_DIR/songs.small" ]]; then
#     #     echo "Song already downloaded and extracted."
#     #     exit 0
#     # fi
#     # data_url="${URL}/llm/playlist_small.tar.gz"
#     # wget --no-check-certificate $data_url -O "$INPUT_DIR"/playlist_small.tar.gz || {
#     #     echo "Failed to download $data_url"
#     #     exit 1
#     # }
#     # tar -xzf "$INPUT_DIR/playlist_small.tar.gz" -C "$INPUT_DIR" || {
#     #     echo "Failed to extract $INPUT_DIR/playlist_small.tar.gz"
#     #     exit 1
#     # }
#     # rm "$INPUT_DIR/playlist_small.tar.gz"
#     # mv "$INPUT_DIR/playlist_small" "$INPUT_DIR/songs.small"
#     # exit 0

# elif [[ "$size" == "min" ]]; then
#     if [[ -d "$INPUT_DIR/jpg.min" ]]; then
#         echo "Image data already downloaded and extracted."
#     else
#         cp -r "${BENCHMARK_DIR}"/min_inputs/jpg.min "$INPUT_DIR"
#     fi
#     # if [[ -d "$INPUT_DIR/songs.min" ]]; then
#     #     echo "Song data already downloaded and extracted."
#     #     exit 0
#     # fi
#     # cp -r "${BENCHMARK_DIR}"/min_inputs/songs.min "$INPUT_DIR"
# else
#     if [[ -d "$INPUT_DIR/jpg" ]]; then
#         echo "Image data already downloaded and extracted."
#     else
#         echo "Downloading full dataset."
#         data_url=https://atlas-group.cs.brown.edu/data/full/jpg.zip
#         zip_dst="$INPUT_DIR/jpg.zip"
#         out_dir="$INPUT_DIR/jpg"
#         wget --no-check-certificate $data_url -O $zip_dst
#         unzip $zip_dst -d $out_dir
#         rm "$zip_dst"
#     fi
#     # if [[ -d "$INPUT_DIR/songs.full" ]]; then
#     #     echo "Song data already downloaded and extracted."
#     #     exit 0
#     # fi
#     # echo "Downloading full dataset."
#     # data_url="${URL}/llm/playlist_full.tar.gz"
#     # wget --no-check-certificate $data_url -O "$INPUT_DIR"/playlist_full.tar.gz || {
#     #     echo "Failed to download $data_url"
#     #     exit 1
#     # }
#     # tar -xzf "$INPUT_DIR/playlist_full.tar.gz" -C "$INPUT_DIR" || {
#     #     echo "Failed to extract $INPUT_DIR/playlist_full.tar.gz"
#     #     exit 1
#     # }
#     # rm "$INPUT_DIR/playlist_full.tar.gz"
#     # mv "$INPUT_DIR/playlist_full" "$INPUT_DIR/songs.full"
# fi
