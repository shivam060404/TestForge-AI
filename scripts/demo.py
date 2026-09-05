#!/usr/bin/env python3
"""
Demo script for Autonomous QA Agent
Shows the complete end-to-end flow:
1. Create project
2. Create environment
3. Generate test from natural language
4. Execute test
5. Simulate selector drift
6. Heal selector
7. Approve healing
8. Rerun and pass using learned memory
9. Detect visual regression or accessibility issue
"""
import asyncio
import uuid
import httpx
from datetime import datetime

API_URL = "http://localhost:8000/api/v1"


class DemoRunner:
    def __init__(self, base_url: str = API_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.project_id = None
        self.environment_id = None
        self.test_case_id = None
        self.run_id = None
    
    async def close(self):
        await self.client.aclose()
    
    async def check_health(self):
        """Check if API is healthy"""
        response = await self.client.get(f"{self.base_url}/health")
        response.raise_for_status()
        print("✓ API is healthy")
        return response.json()
    
    async def create_project(self, name: str, description: str = ""):
        """Create a new project"""
        response = await self.client.post(
            f"{self.base_url}/projects",
            json={"name": name, "description": description}
        )
        response.raise_for_status()
        project = response.json()
        self.project_id = project["id"]
        print(f"✓ Created project: {name} ({self.project_id})")
        return project
    
    async def create_environment(self, name: str, base_url: str):
        """Create a test environment"""
        response = await self.client.post(
            f"{self.base_url}/projects/{self.project_id}/environments",
            json={"name": name, "base_url": base_url}
        )
        response.raise_for_status()
        env = response.json()
        self.environment_id = env["id"]
        print(f"✓ Created environment: {name} -> {base_url}")
        return env
    
    async def generate_test_case(self, intent: str):
        """Generate test case from natural language"""
        response = await self.client.post(
            f"{self.base_url}/projects/{self.project_id}/test-cases/generate",
            json={"intent": intent, "environment_id": self.environment_id}
        )
        response.raise_for_status()
        tc = response.json()
        self.test_case_id = tc["id"]
        print(f"✓ Generated test case: {tc['name']}")
        print(f"  Steps: {len(tc['steps'])}")
        for i, step in enumerate(tc["steps"]):
            print(f"  {i+1}. {step['action']}: {step.get('description', step.get('locator', step.get('target', '')))}")
        return tc
    
    async def execute_test(self):
        """Execute the test case"""
        response = await self.client.post(
            f"{self.base_url}/projects/{self.project_id}/runs",
            json={
                "test_case_id": self.test_case_id,
                "environment_id": self.environment_id,
                "triggered_by": "demo"
            }
        )
        response.raise_for_status()
        run = response.json()
        self.run_id = run["id"]
        print(f"✓ Started test run: {self.run_id}")
        return run
    
    async def wait_for_run_completion(self, timeout: int = 120):
        """Wait for run to complete via polling"""
        start_time = datetime.now()
        while (datetime.now() - start_time).seconds < timeout:
            response = await self.client.get(f"{self.base_url}/runs/{self.run_id}")
            response.raise_for_status()
            run = response.json()
            
            if run["status"] in ("passed", "failed", "cancelled"):
                print(f"✓ Run completed with status: {run['status']}")
                print(f"  Passed: {run['passed_steps']}, Failed: {run['failed_steps']}, Duration: {run.get('duration_ms', 0)}ms")
                return run
            
            print(f"  Run status: {run['status']}...")
            await asyncio.sleep(3)
        
        raise TimeoutError("Run did not complete in time")
    
    async def get_run_details(self):
        """Get detailed run information"""
        response = await self.client.get(f"{self.base_url}/runs/{self.run_id}")
        response.raise_for_status()
        return response.json()
    
    async def list_healing_candidates(self):
        """List healing candidates for the run"""
        response = await self.client.get(f"{self.base_url}/runs/{self.run_id}/healing-candidates")
        response.raise_for_status()
        candidates = response.json()
        print(f"✓ Found {len(candidates)} healing candidate(s)")
        for c in candidates:
            print(f"  - {c['original_locator']} -> {c['suggested_locator']} (confidence: {c['confidence']:.0%})")
        return candidates
    
    async def approve_healing(self, candidate_id: str):
        """Approve a healing candidate"""
        response = await self.client.post(
            f"{self.base_url}/healing-candidates/{candidate_id}/approve",
            json={"candidate_id": candidate_id, "approved": True}
        )
        response.raise_for_status()
        print(f"✓ Approved healing candidate: {candidate_id}")
        return response.json()
    
    async def retry_run(self):
        """Retry the failed run"""
        response = await self.client.post(f"{self.base_url}/runs/{self.run_id}/retry")
        response.raise_for_status()
        new_run = response.json()
        self.run_id = new_run["id"]
        print(f"✓ Retried run: {self.run_id}")
        return new_run
    
    async def get_design_insights(self):
        """Get design intelligence insights"""
        response = await self.client.get(f"{self.base_url}/runs/{self.run_id}/design-insights")
        response.raise_for_status()
        insights = response.json()
        print(f"✓ Design insights retrieved")
        print(f"  Visual comparisons: {len(insights.get('visual_comparisons', []))}")
        print(f"  Accessibility issues: {len(insights.get('accessibility_issues', []))}")
        for issue in insights.get("accessibility_issues", []):
            print(f"  - [{issue['impact'].upper()}] {issue['description']} ({issue['rule_id']})")
        return insights
    
    async def search_memory(self, query: str):
        """Search memory"""
        response = await self.client.post(
            f"{self.base_url}/projects/{self.project_id}/memory/search",
            json={"query": query}
        )
        response.raise_for_status()
        memory = response.json()
        print(f"✓ Memory search results for '{query}':")
        print(f"  Locators: {len(memory.get('locators', []))}")
        print(f"  Episodes: {len(memory.get('episodes', []))}")
        print(f"  Failure patterns: {len(memory.get('failure_patterns', []))}")
        return memory


async def run_demo():
    """Run the complete demo flow"""
    print("=" * 60)
    print("AUTONOMOUS QA AGENT - DEMO FLOW")
    print("=" * 60)
    
    demo = DemoRunner()
    
    try:
        # Step 1: Check health
        print("\n[1/9] Checking API health...")
        await demo.check_health()
        
        # Step 2: Create project
        print("\n[2/9] Creating project...")
        await demo.create_project(
            name="E-commerce Demo",
            description="Demo project for autonomous QA agent showcase"
        )
        
        # Step 3: Create environment
        print("\n[3/9] Creating environment...")
        await demo.create_environment(
            name="Staging",
            base_url="https://demo.playwright.dev/todomvc"
        )
        
        # Step 4: Generate test from natural language
        print("\n[4/9] Generating test case from natural language...")
        await demo.generate_test_case(
            intent="User adds a new todo item, marks it as complete, and filters to show only active todos"
        )
        
        # Step 5: Execute test
        print("\n[5/9] Executing test...")
        await demo.execute_test()
        
        # Step 6: Wait for completion
        print("\n[6/9] Waiting for test completion...")
        run = await demo.wait_for_run_completion()
        
        if run["status"] == "failed":
            # Step 7: Check healing candidates
            print("\n[7/9] Checking for healing candidates...")
            candidates = await demo.list_healing_candidates()
            
            if candidates:
                # Step 8: Approve healing
                print("\n[8/9] Approving healing candidate...")
                await demo.approve_healing(candidates[0]["id"])
                
                # Step 9: Retry run
                print("\n[9/9] Retrying test with healed locator...")
                await demo.retry_run()
                await demo.wait_for_run_completion()
        
        # Get design insights
        print("\n[Design Intelligence] Getting design insights...")
        await demo.get_design_insights()
        
        # Search memory
        print("\n[Memory] Searching learned memory...")
        await demo.search_memory("todo")
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\nProject ID: {demo.project_id}")
        print(f"Test Case ID: {demo.test_case_id}")
        print(f"Final Run ID: {demo.run_id}")
        print(f"\nView results at: http://localhost:3000/runs/{demo.run_id}")
        
    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        raise
    finally:
        await demo.close()


if __name__ == "__main__":
    asyncio.run(run_demo())