{ cd "$(dirname "${0}")/.." ; } || { exit 1 ; }
IMG_DIR="${IMG_DIR}/dpt"
DB_FILE="${OUTPUT_DIR}/db.${MODE}.txt"
CLASS_FILE="${OUTPUT_DIR}/classifications.${MODE}.txt"
mkdir -p "${IMG_DIR}"
/users/jxia3/atlas/incr/target/release/incr --try /users/jxia3/atlas/incr/src/scripts/try.sh --cache /users/jxia3/atlas/incr/evaluation/benchmarks/dpt/cache wget "https://atlas-group.cs.brown.edu/data/dpt/dpt.zip" -O images.zip
/users/jxia3/atlas/incr/target/release/incr --try /users/jxia3/atlas/incr/src/scripts/try.sh --cache /users/jxia3/atlas/incr/evaluation/benchmarks/dpt/cache unzip -o images.zip -d "${IMG_DIR}"
/users/jxia3/atlas/incr/target/release/incr --try /users/jxia3/atlas/incr/src/scripts/try.sh --cache /users/jxia3/atlas/incr/evaluation/benchmarks/dpt/cache rm images.zip
for img in "${IMG_DIR}"/*.jpg; 
 do         cat "${img}" | /users/jxia3/atlas/incr/target/release/incr --try /users/jxia3/atlas/incr/src/scripts/try.sh --cache /users/jxia3/atlas/incr/evaluation/benchmarks/dpt/cache python3 scripts/segment.py | /users/jxia3/atlas/incr/target/release/incr --try /users/jxia3/atlas/incr/src/scripts/try.sh --cache /users/jxia3/atlas/incr/evaluation/benchmarks/dpt/cache python3 scripts/classify.py "${img}" | /users/jxia3/atlas/incr/target/release/incr --try /users/jxia3/atlas/incr/src/scripts/try.sh --cache /users/jxia3/atlas/incr/evaluation/benchmarks/dpt/cache awk "{print \"g:\", \$5}"
done | /users/jxia3/atlas/incr/target/release/incr --try /users/jxia3/atlas/incr/src/scripts/try.sh --cache /users/jxia3/atlas/incr/evaluation/benchmarks/dpt/cache sort > "${DB_FILE}"
