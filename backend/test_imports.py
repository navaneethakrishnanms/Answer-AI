import sys
import traceback
sys.path.insert(0, r'c:\Projects\Paper_AI\backend')

with open('import_error.txt', 'w') as f:
    try:
        from app.schemas.mapping_schema import MappingOutputSchema
        f.write("MappingOutputSchema import OK\n")
    except Exception as e:
        f.write(f"Error importing MappingOutputSchema:\n")
        traceback.print_exc(file=f)

    f.write("\n---\n\n")

    try:
        from app.schemas.evaluation_schema import EvaluationOutputSchema
        f.write("EvaluationOutputSchema import OK\n")
    except Exception as e:
        f.write(f"Error importing EvaluationOutputSchema:\n")
        traceback.print_exc(file=f)

print("Output written to import_error.txt")
