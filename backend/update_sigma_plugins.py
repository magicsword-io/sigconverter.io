#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version


SIGMA_RELEASES_URL = "https://pypi.org/pypi/sigma-cli/json"
PLUGIN_DIRECTORY_URL = "https://raw.githubusercontent.com/SigmaHQ/pySigma-plugin-directory/refs/heads/main/pySigma-plugins-v1.json"
SMOKE_TEST = (
    "from sigma.plugins import InstalledSigmaPlugins; "
    "InstalledSigmaPlugins.autodiscover()"
)
STABLE_VERSION_PATTERN = re.compile(r"^\d+(?:\.\d+)*$")
GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"


class Updater:
    def __init__(self) -> None:
        self.script_dir = Path(__file__).resolve().parent
        self.base_pyproject = self.script_dir / "pyproject.toml"
        self.work_dir = Path(tempfile.mkdtemp(prefix=".update-sigma-plugins.", dir=self.script_dir))
        self.cache_dir = self.work_dir / "cache"
        self.version_cache_dir = self.cache_dir / "versions"
        self.metadata_cache_dir = self.cache_dir / "metadata"
        self.version_cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_cache_dir.mkdir(parents=True, exist_ok=True)
        self.environment = default_environment()

    def cleanup(self) -> None:
        shutil.rmtree(self.work_dir, ignore_errors=True)

    def log_ok(self, package: str, version: str) -> None:
        print(f"  {GREEN}OK{RESET}   {package} -> {version}")

    def log_skip(self, package: str, reason: str) -> None:
        print(f"  {RED}SKIP{RESET} {package} -> {reason}")

    def fetch_json(self, url: str) -> dict | None:
        try:
            with urlopen(url) as response:
                return json.load(response)
        except (HTTPError, URLError):
            return None

    def cache_key(self, package: str) -> str:
        return re.sub(r"[^A-Za-z0-9._-]", "_", package)

    def is_pypi_package(self, package: str) -> bool:
        return not (
            package.startswith("git+")
            or package.startswith("http://")
            or package.startswith("https://")
        )

    def get_sigma_versions(self) -> list[str]:
        payload = self.fetch_json(SIGMA_RELEASES_URL)
        if payload is None:
            raise RuntimeError("Failed to fetch sigma-cli releases from PyPI")

        versions = [
            version
            for version in payload["releases"].keys()
            if "rc" not in version and STABLE_VERSION_PATTERN.match(version)
        ]
        versions.sort(key=Version)
        return versions[-10:]

    def get_plugin_packages(self) -> list[str]:
        payload = self.fetch_json(PLUGIN_DIRECTORY_URL)
        if payload is None:
            raise RuntimeError("Failed to fetch the Sigma plugin directory")
        return sorted(
            {
                plugin["package"]
                for plugin in payload["plugins"].values()
                if isinstance(plugin, dict) and "package" in plugin
            }
        )

    def get_release_versions(self, package: str) -> list[str]:
        if not self.is_pypi_package(package):
            return []

        cache_file = self.version_cache_dir / self.cache_key(package)
        if cache_file.exists():
            return [line for line in cache_file.read_text().splitlines() if line]

        payload = self.fetch_json(f"https://pypi.org/pypi/{package}/json")
        if payload is None:
            cache_file.write_text("")
            return []

        versions = [
            version
            for version in payload["releases"].keys()
            if STABLE_VERSION_PATTERN.match(version)
        ]
        versions.sort(key=Version, reverse=True)
        cache_file.write_text("\n".join(versions))
        return versions

    def get_release_requirements(self, package: str, version: str) -> list[str]:
        if not self.is_pypi_package(package):
            return []

        cache_file = self.metadata_cache_dir / f"{self.cache_key(package)}-{version}.json"
        if cache_file.exists():
            return json.loads(cache_file.read_text())

        payload = self.fetch_json(f"https://pypi.org/pypi/{package}/{version}/json")
        requirements = payload.get("info", {}).get("requires_dist") if payload else None
        if requirements is None:
            requirements = []
        cache_file.write_text(json.dumps(requirements))
        return requirements

    def get_sigma_cli_pysigma_spec(self, sigma_version: str) -> SpecifierSet | None:
        for requirement_text in self.get_release_requirements("sigma-cli", sigma_version):
            requirement = Requirement(requirement_text)
            if requirement.name.lower() == "pysigma":
                return requirement.specifier
        return None

    def get_pysigma_versions(self) -> list[Version]:
        return [Version(version) for version in self.get_release_versions("pysigma")]

    def metadata_allows_target(
        self,
        sigma_version: str,
        sigma_pysigma_spec: SpecifierSet | None,
        requirements: list[str],
        pysigma_versions: list[Version],
    ) -> bool:
        sigma_version_obj = Version(sigma_version)

        for requirement_text in requirements:
            requirement = Requirement(requirement_text)
            if requirement.marker and not requirement.marker.evaluate(self.environment):
                continue

            name = requirement.name.lower()
            if name == "sigma-cli" and requirement.specifier:
                if sigma_version_obj not in requirement.specifier:
                    return False

            if name == "pysigma" and requirement.specifier and sigma_pysigma_spec is not None:
                if not any(
                    version in sigma_pysigma_spec and version in requirement.specifier
                    for version in pysigma_versions
                ):
                    return False

        return True

    def init_project_dir(self, target_dir: Path) -> None:
        shutil.rmtree(target_dir, ignore_errors=True)
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.base_pyproject, target_dir / "pyproject.toml")

    def copy_project_dir(self, source_dir: Path, target_dir: Path) -> None:
        shutil.rmtree(target_dir, ignore_errors=True)
        shutil.copytree(source_dir, target_dir)

    def run_command(self, args: list[str], cwd: Path) -> bool:
        result = subprocess.run(
            args,
            cwd=cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            text=True,
        )
        return result.returncode == 0

    def add_dependency(self, target_dir: Path, dependency: str) -> bool:
        return self.run_command(["uv", "add", "--quiet", "--no-sync", dependency], cwd=target_dir)

    def candidate_locks(self, target_dir: Path) -> bool:
        if not self.run_command(["uv", "lock"], cwd=target_dir):
            return False
        return True

    def project_works(self, target_dir: Path) -> bool:
        if not self.run_command(["uv", "sync", "--frozen", "--no-dev"], cwd=target_dir):
            return False
        return self.run_command(["uv", "run", "python", "-c", SMOKE_TEST], cwd=target_dir)

    def find_plugin_version(
        self,
        sigma_version: str,
        plugin_package: str,
        sigma_pysigma_spec: SpecifierSet | None,
        pysigma_versions: list[Version],
        current_dir: Path,
        test_dir: Path,
    ) -> tuple[str | None, str]:
        metadata_rejected = 0
        available_versions = self.get_release_versions(plugin_package)

        for plugin_version in available_versions:
            requirements = self.get_release_requirements(plugin_package, plugin_version)
            if not self.metadata_allows_target(
                sigma_version,
                sigma_pysigma_spec,
                requirements,
                pysigma_versions,
            ):
                metadata_rejected += 1
                continue

            self.copy_project_dir(current_dir, test_dir)
            if not self.add_dependency(test_dir, f"{plugin_package}=={plugin_version}"):
                continue

            if not self.candidate_locks(test_dir):
                continue

            if self.project_works(test_dir):
                self.copy_project_dir(test_dir, current_dir)
                return plugin_version, ""

        if not available_versions:
            return None, "no PyPI release versions"
        if metadata_rejected == len(available_versions):
            return None, "metadata incompatible"
        return None, "no compatible version found"

    def cleanup_old_versions(self, active_versions: list[str]) -> None:
        active_set = set(active_versions)
        for path in self.script_dir.iterdir():
            if path.is_dir() and STABLE_VERSION_PATTERN.match(path.name) and path.name not in active_set:
                shutil.rmtree(path)

    def update_sigma_version(
        self,
        sigma_version: str,
        plugin_packages: list[str],
        pysigma_versions: list[Version],
    ) -> None:
        print(f"Resolving plugins for sigma-cli version: {sigma_version}")

        sigma_pysigma_spec = self.get_sigma_cli_pysigma_spec(sigma_version)
        current_dir = self.work_dir / f"current-{sigma_version}"
        test_dir = self.work_dir / f"test-{sigma_version}"
        version_dir = self.script_dir / sigma_version
        accepted_count = 0
        skipped_count = 0

        self.init_project_dir(current_dir)
        if not self.add_dependency(current_dir, f"sigma-cli=={sigma_version}"):
            print(f"Skipping sigma-cli version {sigma_version} because it could not be added")
            return

        for plugin_package in plugin_packages:
            plugin_version, skip_reason = self.find_plugin_version(
                sigma_version,
                plugin_package,
                sigma_pysigma_spec,
                pysigma_versions,
                current_dir,
                test_dir,
            )
            if plugin_version is not None:
                self.log_ok(plugin_package, plugin_version)
                accepted_count += 1
            else:
                self.log_skip(plugin_package, skip_reason)
                skipped_count += 1

        self.copy_project_dir(current_dir, version_dir)
        print(f"Completed {sigma_version}: accepted={accepted_count} skipped={skipped_count}")

    def run(self) -> None:
        sigma_versions = self.get_sigma_versions()
        plugin_packages = self.get_plugin_packages()
        pysigma_versions = self.get_pysigma_versions()

        for sigma_version in sigma_versions:
            self.update_sigma_version(sigma_version, plugin_packages, pysigma_versions)

        self.cleanup_old_versions(sigma_versions)


def main() -> int:
    updater = Updater()
    try:
        updater.run()
    finally:
        updater.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
