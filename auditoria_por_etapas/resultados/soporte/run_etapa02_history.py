"""Run history preservation test in the isolated memory-only runner."""
import run_etapa02_revalidacion as runner

runner.LABELS = ["identity.test_audit02_history"]
runner.EXECUTION_NAME = "02-B-conservacion-historial"
if __name__ == "__main__":
    raise SystemExit(runner.main())
