"""Tests for GitHub Actions workflow configuration."""

import unittest
import yaml
import os
from pathlib import Path


class TestWorkflowConfiguration(unittest.TestCase):
    """Test suite for validating GitHub Actions workflow files."""
    
    @classmethod
    def setUpClass(cls):
        """Load workflow files for testing."""
        cls.workflow_dir = Path(__file__).parent.parent / '.github' / 'workflows'
        cls.build_workflow_path = cls.workflow_dir / 'build.yml'
        
        # Load build workflow
        with open(cls.build_workflow_path, 'r') as f:
            cls.build_workflow = yaml.safe_load(f)
    
    def test_build_workflow_exists(self):
        """Test that build.yml workflow exists."""
        self.assertTrue(
            self.build_workflow_path.exists(),
            "build.yml workflow file should exist"
        )
    
    def test_build_workflow_valid_yaml(self):
        """Test that build.yml is valid YAML."""
        self.assertIsNotNone(
            self.build_workflow,
            "build.yml should be valid YAML"
        )
    
    def test_build_workflow_has_required_triggers(self):
        """Test that build workflow has correct triggers."""
        # YAML parses 'on' as True (boolean), so we check for True key
        self.assertIn(True, self.build_workflow)
        triggers = self.build_workflow[True]
        
        # Should have pull_request trigger
        self.assertIn('pull_request', triggers)
        self.assertIn('branches', triggers['pull_request'])
        self.assertIn('main', triggers['pull_request']['branches'])
        self.assertIn('types', triggers['pull_request'])
        self.assertIn('closed', triggers['pull_request']['types'])
        
        # Should have workflow_dispatch for manual triggers
        self.assertIn('workflow_dispatch', triggers)
        self.assertIn('inputs', triggers['workflow_dispatch'])
        
        # Check workflow_dispatch inputs
        inputs = triggers['workflow_dispatch']['inputs']
        self.assertIn('version_type', inputs)
    
    def test_build_workflow_has_test_job(self):
        """Test that build workflow has a test job."""
        self.assertIn('jobs', self.build_workflow)
        jobs = self.build_workflow['jobs']
        self.assertIn('test', jobs)
        
        test_job = jobs['test']
        self.assertIn('runs-on', test_job)
        self.assertEqual(test_job['runs-on'], 'ubuntu-latest')
        
        # Should run unit tests
        steps = test_job['steps']
        test_step_names = [step.get('name', '') for step in steps]
        self.assertTrue(
            any('unit test' in name.lower() for name in test_step_names),
            "Test job should include a unit test step"
        )
    
    def test_build_workflow_has_platform_builds(self):
        """Test that build workflow builds for all required platforms."""
        jobs = self.build_workflow['jobs']
        
        # Should have Linux build job
        self.assertIn('build-linux', jobs)
        linux_job = jobs['build-linux']
        self.assertIn('strategy', linux_job)
        self.assertIn('matrix', linux_job['strategy'])
        linux_archs = linux_job['strategy']['matrix']['arch']
        self.assertIn('x86_64', linux_archs, "Should build for Linux x86_64")
        self.assertIn('i686', linux_archs, "Should build for Linux i686")
        self.assertIn('arm64', linux_archs, "Should build for Linux arm64")
        
        # Windows and macOS build jobs removed due to python-olm build issues
        self.assertNotIn('build-windows', jobs, "Windows builds removed")
        self.assertNotIn('build-macos', jobs, "macOS builds removed")
    
    def test_build_workflow_uses_nuitka_action(self):
        """Test that build workflow uses Nuitka-Action."""
        jobs = self.build_workflow['jobs']
        
        # Check Linux build job for Nuitka-Action usage (Windows/macOS removed)
        for job_name in ['build-linux']:
            job = jobs[job_name]
            steps = job['steps']
            
            # Find Nuitka build steps
            nuitka_steps = [
                step for step in steps
                if 'uses' in step and 'Nuitka' in step['uses']
            ]
            
            # Should have at least one Nuitka step
            self.assertGreater(
                len(nuitka_steps), 0,
                f"{job_name} should use Nuitka-Action"
            )
            
            # Check Nuitka configuration
            for nuitka_step in nuitka_steps:
                with_config = nuitka_step.get('with', {})
                self.assertIn('script-name', with_config)
                self.assertIn('mode', with_config)
                self.assertEqual(with_config['mode'], 'onefile')
    
    def test_build_workflow_has_version_calculation(self):
        """Test that build workflow calculates versions correctly."""
        jobs = self.build_workflow['jobs']
        
        # Check Linux build job has version calculation (Windows/macOS removed)
        for job_name in ['build-linux']:
            job = jobs[job_name]
            steps = job['steps']
            
            version_steps = [
                step for step in steps
                if 'Calculate version' in step.get('name', '')
            ]
            
            self.assertGreater(
                len(version_steps), 0,
                f"{job_name} should calculate version"
            )
    
    def test_build_workflow_has_release_job(self):
        """Test that build workflow has a release job."""
        jobs = self.build_workflow['jobs']
        self.assertIn('release', jobs)
        
        release_job = jobs['release']
        
        # Should depend on all build jobs (Linux only)
        self.assertIn('needs', release_job)
        needs = release_job['needs']
        self.assertIn('build-linux', needs)
        # Windows and macOS builds removed due to python-olm build issues
        self.assertNotIn('build-windows', needs)
        self.assertNotIn('build-macos', needs)
        
        # Should download artifacts
        steps = release_job['steps']
        download_steps = [
            step for step in steps
            if 'download' in step.get('name', '').lower()
        ]
        self.assertGreater(
            len(download_steps), 0,
            "Release job should download artifacts"
        )
        
        # Should create GitHub release
        gh_release_steps = [
            step for step in steps
            if 'uses' in step and 'action-gh-release' in step['uses']
        ]
        self.assertGreater(
            len(gh_release_steps), 0,
            "Release job should create GitHub release"
        )
    
    def test_build_workflow_has_metadata(self):
        """Test that build workflow includes appropriate metadata (Windows build removed)."""
        # Windows and macOS builds removed due to python-olm build issues
        # This test is kept for potential future re-enablement but currently skipped
        self.skipTest("Windows and macOS builds removed - test no longer applicable")
    
    def test_build_workflow_includes_assets(self):
        """Test that build workflow includes assets directory."""
        jobs = self.build_workflow['jobs']
        
        # Check Linux build job for assets (Windows/macOS removed)
        for job_name in ['build-linux']:
            job = jobs[job_name]
            steps = job['steps']
            
            nuitka_steps = [
                step for step in steps
                if 'uses' in step and 'Nuitka' in step['uses']
            ]
            
            for nuitka_step in nuitka_steps:
                with_config = nuitka_step.get('with', {})
                self.assertIn('include-data-dir', with_config)
                
                # Check that assets are included
                include_data = with_config['include-data-dir']
                if isinstance(include_data, str):
                    self.assertIn('assets', include_data)
                elif isinstance(include_data, list):
                    self.assertTrue(
                        any('assets' in item for item in include_data)
                    )
    
    def test_build_workflow_moves_x86_64_artifact(self):
        """Test that build workflow moves x86_64 artifact from build/ directory."""
        jobs = self.build_workflow['jobs']
        linux_job = jobs['build-linux']
        steps = linux_job['steps']
        
        # Find the move step for x86_64
        move_steps = [
            step for step in steps
            if 'Move x86_64 artifact to root' in step.get('name', '')
        ]
        
        self.assertGreater(
            len(move_steps), 0,
            "Linux build should have a step to move x86_64 artifact to root"
        )
        
        # Verify the move step has the correct if condition
        move_step = move_steps[0]
        self.assertIn('if', move_step)
        self.assertIn('x86_64', move_step['if'])
        
        # Verify the move step has the correct run command
        self.assertIn('run', move_step)
        run_command = move_step['run']
        self.assertIn('mv', run_command)
        self.assertIn('build/chatrixcd-linux-x86_64', run_command)
        self.assertIn('./chatrixcd-linux-x86_64', run_command)


class TestIconFiles(unittest.TestCase):
    """Test suite for validating icon files."""
    
    @classmethod
    def setUpClass(cls):
        """Setup paths to icon files."""
        cls.assets_dir = Path(__file__).parent.parent / 'assets'
        cls.icon_ico_path = cls.assets_dir / 'icon.ico'
        cls.icon_png_path = cls.assets_dir / 'icon.png'
    
    def test_icon_ico_exists(self):
        """Test that icon.ico exists for Windows builds."""
        self.assertTrue(
            self.icon_ico_path.exists(),
            "icon.ico should exist for Windows builds"
        )
    
    def test_icon_png_exists(self):
        """Test that icon.png exists for macOS/Linux builds."""
        self.assertTrue(
            self.icon_png_path.exists(),
            "icon.png should exist for macOS/Linux builds"
        )
    
    def test_icon_ico_is_valid(self):
        """Test that icon.ico is a valid ICO file."""
        if not self.icon_ico_path.exists():
            self.skipTest("icon.ico does not exist")
        
        with open(self.icon_ico_path, 'rb') as f:
            # ICO files start with 0x00 0x00 0x01 0x00
            header = f.read(4)
            self.assertEqual(
                header[:2], b'\x00\x00',
                "ICO file should start with 0x00 0x00"
            )
            self.assertEqual(
                header[2:4], b'\x01\x00',
                "ICO file should have type 0x01 0x00"
            )
    
    def test_icon_png_is_valid(self):
        """Test that icon.png is a valid PNG file."""
        if not self.icon_png_path.exists():
            self.skipTest("icon.png does not exist")
        
        with open(self.icon_png_path, 'rb') as f:
            # PNG files start with PNG signature
            header = f.read(8)
            self.assertEqual(
                header, b'\x89PNG\r\n\x1a\n',
                "PNG file should have correct signature"
            )


if __name__ == '__main__':
    unittest.main()
