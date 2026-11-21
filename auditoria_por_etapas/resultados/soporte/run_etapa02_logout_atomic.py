"""Run logout atomicity tests in the isolated memory-only runner."""
import run_etapa02_revalidacion as runner

runner.LABELS = ["identity.test_audit02_logout_atomic"]
runner.EXECUTION_NAME = "02-B-atomicidad-salida"
if __name__ == "__main__":
    raise SystemExit(runner.main())
