"""Run field and session boundary tests in the established memory-only runner."""
import run_etapa02_revalidacion as runner

runner.LABELS = ["identity.test_audit02_boundaries"]
runner.EXECUTION_NAME = "02-B-fronteras-y-sesiones"
if __name__ == "__main__":
    raise SystemExit(runner.main())
