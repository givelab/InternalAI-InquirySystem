SCRIPT_DIR=$(dirname $0)

rm $SCRIPT_DIR/../migrations/versions/a4cba4ed338c_add_user_data.py
rm $SCRIPT_DIR/../src/models/users.py
rm $SCRIPT_DIR/../src/crud/users.py
rm $SCRIPT_DIR/../src/schemas/users.py
rm $SCRIPT_DIR/../src/services/users.py
rm $SCRIPT_DIR/../src/routers/users.py
rm $SCRIPT_DIR/../tests/unit/crud/test_users.py
rm $SCRIPT_DIR/../tests/unit/services/test_users.py
rm $SCRIPT_DIR/../tests/unit/routers/test_users.py
rm $SCRIPT_DIR/../tests/integration/test_users.py
rm $SCRIPT_DIR/../tests/factories/models/users.py

patch -p1 < $SCRIPT_DIR/patches/remove_sample_implementation.patch
