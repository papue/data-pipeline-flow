"""Allow: python -m data_pipeline_flow <command>"""
from data_pipeline_flow.cli.main import main
import sys

if __name__ == "__main__":
    sys.exit(main())
