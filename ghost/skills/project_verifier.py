import json
from pathlib import Path
import subprocess
from typing import Any, Dict, List


SAFE_NODE_SCRIPTS = {
    "lint",
    "test",
    "build",
}

IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
}


def run_command(
    command: List[str],
    cwd: str,
    timeout: int = 120,
) -> Dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        return {
            "command": command,
            "cwd": cwd,
            "success": completed.returncode == 0,
            "return_code": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }

    except subprocess.TimeoutExpired:
        return {
            "command": command,
            "cwd": cwd,
            "success": False,
            "return_code": None,
            "stdout": "",
            "stderr": (
                f"Command timed out after "
                f"{timeout} seconds."
            ),
        }


def read_package_json(
    package_path: Path,
) -> Dict[str, Any]:
    try:
        with open(
            package_path,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        return {
            "name": data.get("name"),
            "scripts": data.get(
                "scripts",
                {},
            ),
            "dependencies": sorted(
                data.get(
                    "dependencies",
                    {},
                ).keys()
            ),
            "dev_dependencies": sorted(
                data.get(
                    "devDependencies",
                    {},
                ).keys()
            ),
        }

    except (
        json.JSONDecodeError,
        OSError,
    ) as error:
        return {
            "error": str(error),
        }


def detect_component(
    component_path: Path,
) -> Dict[str, Any]:
    detected_files: List[str] = []
    project_types = set()

    markers = {
        "requirements.txt": "python",
        "pyproject.toml": "python",
        "manage.py": "django",
        "package.json": "node",
        "vite.config.js": "vite",
        "vite.config.ts": "vite",
        "vite.config.mjs": "vite",
    }

    for filename, project_type in markers.items():
        path = component_path / filename

        if path.exists():
            detected_files.append(filename)
            project_types.add(project_type)

    component: Dict[str, Any] = {
        "path": str(component_path),
        "project_types": sorted(
            project_types
        ),
        "detected_files": detected_files,
    }

    package_path = (
        component_path
        / "package.json"
    )

    if package_path.exists():
        component["package"] = (
            read_package_json(
                package_path
            )
        )

    return component


def discover_components(
    project_path: str,
) -> List[Dict[str, Any]]:
    root = (
        Path(project_path)
        .expanduser()
        .resolve()
    )

    if not root.exists():
        raise FileNotFoundError(
            f"Project does not exist: {root}"
        )

    if not root.is_dir():
        raise NotADirectoryError(
            f"Project path is not a directory: {root}"
        )

    components: List[
        Dict[str, Any]
    ] = []

    root_component = detect_component(
        root
    )

    if (
        root_component["project_types"]
        or root_component["detected_files"]
    ):
        root_component["name"] = "root"

        components.append(
            root_component
        )

    for child in sorted(
        root.iterdir()
    ):
        if not child.is_dir():
            continue

        if child.name in IGNORED_DIRECTORIES:
            continue

        component = detect_component(
            child
        )

        if not component[
            "project_types"
        ]:
            continue

        component["name"] = child.name

        components.append(
            component
        )

    return components


def inspect_git_status(
    project_path: str,
) -> Dict[str, Any]:
    return run_command(
        [
            "git",
            "status",
            "--short",
        ],
        cwd=project_path,
    )


def build_verification_plan(
    components: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    plan: List[Dict[str, Any]] = []

    for component in components:
        component_path = component["path"]

        project_types = set(
            component["project_types"]
        )

        if "python" in project_types:
            plan.append({
                "name": "python_compile",
                "component": component["name"],
                "cwd": component_path,
                "command": [
                    "python",
                    "-m",
                    "compileall",
                    "-q",
                    ".",
                ],
            })

        if "node" in project_types:
            package = component.get(
                "package",
                {},
            )

            scripts = package.get(
                "scripts",
                {},
            )

            for script_name in SAFE_NODE_SCRIPTS:
                if script_name not in scripts:
                    continue

                plan.append({
                    "name": f"npm_{script_name}",
                    "component": component["name"],
                    "cwd": component_path,
                    "command": [
                        "npm",
                        "run",
                        script_name,
                    ],
                })

    return plan


def run_verification_plan(
    plan: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    for check in plan:
        print(
            f"👻 CHECK → "
            f"{check['component']} / "
            f"{check['name']}"
        )

        result = run_command(
            check["command"],
            cwd=check["cwd"],
        )

        result["name"] = check["name"]
        result["component"] = check["component"]

        results.append(result)

        if result["success"]:
            print(
                f"✅ PASS → "
                f"{check['name']}"
            )
        else:
            print(
                f"❌ FAIL → "
                f"{check['name']}"
            )

    return results


def summarize_verification(
    results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    total = len(results)

    passed = sum(
        1
        for result in results
        if result["success"]
    )

    failed = total - passed

    return {
        "total_checks": total,
        "passed": passed,
        "failed": failed,
        "success": (
            total > 0
            and failed == 0
        ),
    }


def inspect_project(
    project_path: str,
) -> Dict[str, Any]:
    root = (
        Path(project_path)
        .expanduser()
        .resolve()
    )

    components = discover_components(
        str(root)
    )

    git_status = inspect_git_status(
        str(root)
    )

    detected_types = sorted({
        project_type

        for component in components

        for project_type in component[
            "project_types"
        ]
    })

    return {
        "project_path": str(root),
        "project_types": detected_types,
        "components": components,
        "git_status": git_status,
    }


def verify_project(
    project_path: str,
) -> Dict[str, Any]:
    print()
    print(
        "👻 GHOST PROJECT VERIFIER"
    )
    print(
        "-------------------------"
    )

    inspection = inspect_project(
        project_path
    )

    plan = build_verification_plan(
        inspection["components"]
    )

    print(
        f"👻 PLAN → "
        f"{len(plan)} checks"
    )

    results = run_verification_plan(
        plan
    )

    summary = summarize_verification(
        results
    )

    return {
        "project": inspection,
        "plan": plan,
        "checks": results,
        "summary": summary,
    }