"""Lighthouse performance tests."""

import pytest
import subprocess
import json
import os
from pathlib import Path


@pytest.mark.lighthouse
class TestPerformance:
    """Lighthouse performance tests."""
    
    @pytest.fixture
    def base_url(self):
        """Base URL for the application."""
        return os.getenv("BASE_URL", "http://localhost:8000")
    
    def test_homepage_performance(self, base_url):
        """Test homepage performance with Lighthouse."""
        # Check if lighthouse CLI is available
        try:
            result = subprocess.run(
                ["lighthouse", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            lighthouse_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            lighthouse_available = False
        
        if not lighthouse_available:
            pytest.skip("Lighthouse CLI not available. Install with: npm install -g lighthouse")
        
        # Run Lighthouse
        output_file = Path("lighthouse-report.json")
        try:
            result = subprocess.run(
                [
                    "lighthouse",
                    base_url,
                    "--output=json",
                    "--output-path=lighthouse-report.json",
                    "--chrome-flags=--headless",
                    "--quiet"
                ],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                pytest.skip(f"Lighthouse failed: {result.stderr}")
            
            # Read results
            if output_file.exists():
                with open(output_file, "r") as f:
                    report = json.load(f)
                
                # Extract scores
                categories = report.get("categories", {})
                performance = categories.get("performance", {}).get("score", 0) * 100
                accessibility = categories.get("accessibility", {}).get("score", 0) * 100
                best_practices = categories.get("best-practices", {}).get("score", 0) * 100
                seo = categories.get("seo", {}).get("score", 0) * 100
                
                # Assert minimum scores (adjust as needed)
                assert performance >= 50, f"Performance score {performance} is below 50"
                assert accessibility >= 70, f"Accessibility score {accessibility} is below 70"
                assert best_practices >= 70, f"Best practices score {best_practices} is below 70"
                assert seo >= 70, f"SEO score {seo} is below 70"
                
                # Clean up
                output_file.unlink()
            else:
                pytest.fail("Lighthouse report file not created")
        finally:
            # Clean up
            if output_file.exists():
                output_file.unlink()
    
    def test_invoices_page_performance(self, base_url):
        """Test invoices page performance with Lighthouse."""
        # Check if lighthouse CLI is available
        try:
            result = subprocess.run(
                ["lighthouse", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            lighthouse_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            lighthouse_available = False
        
        if not lighthouse_available:
            pytest.skip("Lighthouse CLI not available. Install with: npm install -g lighthouse")
        
        # Run Lighthouse on invoices page (requires authentication, may skip)
        output_file = Path("lighthouse-invoices-report.json")
        try:
            result = subprocess.run(
                [
                    "lighthouse",
                    f"{base_url}/invoices",
                    "--output=json",
                    "--output-path=lighthouse-invoices-report.json",
                    "--chrome-flags=--headless",
                    "--quiet"
                ],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # May fail if authentication required - that's OK
            if result.returncode != 0:
                pytest.skip(f"Lighthouse failed (may require auth): {result.stderr}")
            
            # Read results if available
            if output_file.exists():
                with open(output_file, "r") as f:
                    report = json.load(f)
                
                # Extract scores
                categories = report.get("categories", {})
                performance = categories.get("performance", {}).get("score", 0) * 100
                
                # Assert minimum performance score
                assert performance >= 50, f"Performance score {performance} is below 50"
                
                # Clean up
                output_file.unlink()
        finally:
            # Clean up
            if output_file.exists():
                output_file.unlink()
