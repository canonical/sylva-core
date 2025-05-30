# Chainsaw Policy Test Suite

This repository contains a set of [Kyverno Chainsaw](https://kyverno.github.io/chainsaw/) tests for validating Kubernetes admission policies. The structure, naming, and security practices are designed for clarity, maintainability, and minimal risk.

---

## How to Use

### 1. Structure and Naming

- **Test directories and files are named to match the admission policy they validate.**
  - Example: `tests/02-disallow-default-namespace/chainsaw-test.yaml` tests the `disallow-default-namespace` policy that denies the use of the `default` namespace.
- **Resource manifests** (Pods, Deployments, etc.) are named to reflect the policy and scenario, e.g. `disallow-default-namespace-pod.yaml`.
- **This naming convention makes it easy to correlate tests and resources with the policies they cover.**

### 2. Running Tests

- Use the provided Kustomize setup to deploy all test resources in a secure, isolated namespace.
- Apply all resources (including RBAC, namespace, ConfigMaps, and the Chainsaw Job) using:
  ```sh
  kubectl apply -k kustomization/base
  ```
- To clean up all test resources after the run, use:
  ```sh
  kubectl delete -k kustomization/base
  ```

#### About `kustomization.yaml`

- The `kustomization.yaml` file in `kustomization/base` defines all resources and configuration needed for the test suite.
- It references:
  - The Chainsaw Job manifest
  - The test namespace
  - All required ConfigMaps (including test definitions and manifests)
- It uses `configMapGenerator` with `disableNameSuffixHash: true` to ensure predictable ConfigMap names.
- You can add or remove resources and ConfigMaps in `kustomization.yaml` to control what gets deployed for testing.
- This approach makes it easy to manage, version, and reproduce your test environment with a single command.

- Example commands for linting tests (requires installing the Chainsaw binary locally):
  ```sh
  chainsaw lint test -f kustomization/base/tests/01-disallow-latest-tag/chainsaw-test.yaml
  ```
  You can download the Chainsaw binary from the [official releases page](https://github.com/kyverno/chainsaw/releases).

### 3. Security Best Practices

- **ClusterRole is limited only to testing use cases.**
  - RBAC permissions are scoped to only the resources and verbs required for the tests.
  - Impersonation is restricted to only the necessary ServiceAccounts (e.g., `cert-manager-cainjector`).
- **Resources are secured to limit any risk.**
  - All test Pods and controllers use strict `securityContext` settings:
    - `runAsNonRoot: true`
    - `readOnlyRootFilesystem: true`
    - `allowPrivilegeEscalation: false`
    - `capabilities.drop: ["ALL"]`
    - `seccompProfile.type: RuntimeDefault`
  - Resource requests and limits are always set.

### 4. Global Chainsaw Configuration

The global config file is located at [`tests/.chainsaw.yaml`](tests/.chainsaw.yaml):

```yaml
apiVersion: chainsaw.kyverno.io/v1alpha2
kind: Configuration
metadata:
  name: configuration
spec:
  # Global test execution settings
  timeouts:
    apply: 20s
    cleanup: 20s
    delete: 20s
  cleanup:
    skipDelete: false
    delayBeforeCleanup: 10s
  execution:
    failFast: true
    parallel: 1
    repeatCount: 1
  discovery:
    # To exclude redundant tests caused by volume mount in the pods
    excludeTestRegex: chainsaw/#01$
  namespace:
    name: chainsaw-test
    template:
      metadata:
        labels:
          app: chainsaw-tests
  report:
    format: JSON
    name: chainsaw-report
    path: /tmp/chainsaw-report
```

- **Key options:**
  - `failFast: true` — Stop on first test failure.
  - `parallel: 1` — Run tests sequentially to avoid API overload.
  - `skipDelete: false` — Always clean up resources after tests.
  - `delayBeforeCleanup: 10s` — Wait before cleanup to allow for resource finalization.

### 5. Preventing Excessive Retries

- Set reasonable timeouts for `apply`, `delete`, and `cleanup`.
- Insert `sleep` steps between deletes and applies to avoid rapid re-applies.
- Wait for resource deletion before re-creating resources.
- Use `failFast` and `parallel: 1` to avoid cascading failures and API rate limiting.

### 6. Writing New Tests

- Use the template in `tests/00-reference/chainsaw-test.yaml` as a starting point.
- Update the short description at the top of each test file to match the policy/scenario.
- Always include cleanup steps (when using the `skipDelete: true` option) and a sleep step at the end of each test to avoid rate limiting.

---

## Summary

- **Naming is correlated to admission policy** for clarity and traceability.
- **ClusterRole is limited only to testing use cases** for least-privilege security.
- **Resources are secured to limit any risk** using strict security contexts and resource limits.
- **Global config options** are set for reliable, reproducible, and safe test execution.

For more details, see the comments and examples in each test and manifest file.