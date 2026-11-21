"""Final regression of identity, cash and sales, including stage02 audit tests."""
import run_etapa02_revalidacion as runner

runner.LABELS = [
    "identity.tests", "identity.test_auth_audit01", "identity.test_etapa02_audit",
    "identity.test_etapa02_estado", "identity.test_audit02_boundaries",
    "identity.test_audit02_logout_atomic", "identity.test_audit02_history", "cash.tests", "sales.tests",
]
runner.EXECUTION_NAME = "02-D-regresion-final-identidad-caja-ventas"
if __name__ == "__main__":
    raise SystemExit(runner.main())
