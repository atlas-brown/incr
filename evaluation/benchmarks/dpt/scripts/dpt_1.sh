{ cd "$(dirname "${0}")/.." ; } || { exit 1 ; }
IMG_DIR="${IMG_DIR}/dpt"
DB_FILE="${OUTPUT_DIR}/db.${MODE}.txt"
CLASS_FILE="${OUTPUT_DIR}/classifications.${MODE}.txt"
mkdir -p "${IMG_DIR}"
/users/jxia3/atlas/incr/target/release/incr --try /users/jxia3/atlas/incr/src/scripts/try.sh --cache /users/jxia3/atlas/incr/evaluation/benchmarks/dpt/cache --observe /users/jxia3/atlas/incr/../observe/target/release/observe wget "https://atlas-group.cs.brown.edu/data/dpt/dpt.zip" -O images.zip
/users/jxia3/atlas/incr/target/release/incr --try /users/jxia3/atlas/incr/src/scripts/try.sh --cache /users/jxia3/atlas/incr/evaluation/benchmarks/dpt/cache --observe /users/jxia3/atlas/incr/../observe/target/release/observe unzip -o images.zip -d "${IMG_DIR}"
/users/jxia3/atlas/incr/target/release/incr --try /users/jxia3/atlas/incr/src/scripts/try.sh --cache /users/jxia3/atlas/incr/evaluation/benchmarks/dpt/cache --observe /users/jxia3/atlas/incr/../observe/target/release/observe rm images.zip
/users/jxia3/atlas/incr/target/release/incr --try /users/jxia3/atlas/incr/src/scripts/try.sh --cache /users/jxia3/atlas/incr/evaluation/benchmarks/dpt/cache --observe /users/jxia3/atlas/incr/../observe/target/release/observe mogrify -resize 1024x1024\> "${IMG_DIR}"/*.jpg
for img in "${IMG_DIR}"/*.jpg; 
 do         cat "${img}" | /users/jxia3/atlas/incr/target/release/incr --try /users/jxia3/atlas/incr/src/scripts/try.sh --cache /users/jxia3/atlas/incr/evaluation/benchmarks/dpt/cache --observe /users/jxia3/atlas/incr/../observe/target/release/observe python3 scripts/segment.py | /users/jxia3/atlas/incr/target/release/incr --try /users/jxia3/atlas/incr/src/scripts/try.sh --cache /users/jxia3/atlas/incr/evaluation/benchmarks/dpt/cache --observe /users/jxia3/atlas/incr/../observe/target/release/observe python3 scripts/classify.py "${img}" | /users/jxia3/atlas/incr/target/release/incr --try /users/jxia3/atlas/incr/src/scripts/try.sh --cache /users/jxia3/atlas/incr/evaluation/benchmarks/dpt/cache --observe /users/jxia3/atlas/incr/../observe/target/release/observe awk "{print \"g:\", \$5}"
done | /users/jxia3/atlas/incr/target/release/incr --try /users/jxia3/atlas/incr/src/scripts/try.sh --cache /users/jxia3/atlas/incr/evaluation/benchmarks/dpt/cache --observe /users/jxia3/atlas/incr/../observe/target/release/observe sort > "${DB_FILE}"
