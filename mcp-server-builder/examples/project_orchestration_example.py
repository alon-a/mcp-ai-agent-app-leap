#!/usr/bin/env python3
"""
Example demonstrating the project orchestration and management capabilities.

This example shows how to use the ProjectManagerImpl to create an MCP server
with full progress tracking, error handling, and recovery coordination.
"""

import os
import sys
import tempfile

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.managers import ProjectManagerImpl, LogLevel


def progress_callback(project_id: str, percentage: float, phase: str):
    """Callback to handle progress updates."""
    print(f"[{project_id}] {phase}: {percentage:.1f}%")


def error_callback(project_id: str, error_message: str):
    """Callback to handle error notifications."""
    print(f"[{project_id}] ERROR: {error_message}")


def main():
    """Demonstrate project orchestration capabilities."""
    print("=== MCP Server Builder - Project Orchestration Example ===\n")
    
    # Create a temporary directory for the example
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temporary directory: {temp_dir}\n")
        
        # Initialize the project manager with callbacks
        project_manager = ProjectManagerImpl(
            progress_callback=progress_callback,
            error_callback=error_callback,
            log_level=LogLevel.INFO
        )
        
        print("1. Project Manager initialized with:")
        print("   - Progress tracking enabled")
        print("   - Error handling and recovery coordination")
        print("   - Centralized logging\n")
        
        # Example 1: List available projects (should be empty initially)
        print("2. Listing existing projects:")
        projects = project_manager.list_projects()
        if projects:
            for project in projects:
                print(f"   - {project['name']} ({project['status']})")
        else:
            print("   No existing projects found\n")
        
        # Example 2: Demonstrate error handling
        print("3. Demonstrating error handling:")
        try:
            # This will fail because the template doesn't exist
            result = project_manager.create_project(
                name="example-server",
                template="nonexistent-template",
                config={
                    'output_directory': temp_dir,
                    'custom_settings': {
                        'server_name': 'Example MCP Server',
                        'description': 'An example MCP server'
                    }
                }
            )
            
            print(f"   Project creation result: {'SUCCESS' if result.success else 'FAILED'}")
            if not result.success:
                print(f"   Project ID: {result.project_id}")
                print(f"   Status: {result.status.value}")
                print("   Errors:")
                for error in result.errors:
                    print(f"     - {error}")
        
        except Exception as e:
            print(f"   Unexpected error: {e}")
        
        print()
        
        # Example 3: Demonstrate progress tracking
        print("4. Demonstrating progress tracking:")
        
        # Get the project ID from the failed attempt
        projects = project_manager.list_projects()
        if projects:
            project_id = projects[0]['project_id']
            
            # Get progress information
            progress_info = project_manager.get_project_progress(project_id)
            if progress_info:
                print(f"   Project: {progress_info['project_id']}")
                print(f"   Current phase: {progress_info['current_phase']}")
                print(f"   Progress: {progress_info['current_percentage']:.1f}%")
                print(f"   Phases completed: {progress_info['phases_completed']}")
                print(f"   Errors: {progress_info['error_count']}")
                print(f"   Warnings: {progress_info['warning_count']}")
        
        print()
        
        # Example 4: Demonstrate error analysis
        print("5. Demonstrating error analysis:")
        if projects:
            project_id = projects[0]['project_id']
            
            # Get detailed error information
            errors = project_manager.get_project_errors(project_id)
            print(f"   Total errors for project: {len(errors)}")
            
            for i, error in enumerate(errors[:3], 1):  # Show first 3 errors
                print(f"   Error {i}:")
                print(f"     Category: {error['category']}")
                print(f"     Severity: {error['severity']}")
                print(f"     Message: {error['message']}")
                print(f"     Phase: {error['phase']}")
                if error['suggested_actions']:
                    print(f"     Suggested actions:")
                    for action in error['suggested_actions'][:2]:  # Show first 2 actions
                        print(f"       - {action}")
        
        print()
        
        # Example 5: Demonstrate cleanup
        print("6. Demonstrating project cleanup:")
        if projects:
            project_id = projects[0]['project_id']
            
            print(f"   Cleaning up project: {project_id}")
            success = project_manager.cleanup_project(project_id)
            print(f"   Cleanup result: {'SUCCESS' if success else 'FAILED'}")
            
            # Verify cleanup
            remaining_projects = project_manager.list_projects()
            print(f"   Remaining projects: {len(remaining_projects)}")
        
        print()
        
        # Example 6: Demonstrate rollback functionality
        print("7. Demonstrating rollback functionality:")
        
        # Register some rollback actions
        test_project_id = "rollback-test-project"
        rollback_results = []
        
        def test_rollback_1():
            rollback_results.append("Rollback action 1 executed")
            return True
        
        def test_rollback_2():
            rollback_results.append("Rollback action 2 executed")
            return True
        
        project_manager.error_handler.register_rollback_action(test_project_id, test_rollback_1)
        project_manager.error_handler.register_rollback_action(test_project_id, test_rollback_2)
        
        print(f"   Registered rollback actions for: {test_project_id}")
        
        # Execute rollback
        success = project_manager.force_rollback(test_project_id)
        print(f"   Rollback execution result: {'SUCCESS' if success else 'FAILED'}")
        print(f"   Rollback actions executed: {len(rollback_results)}")
        for result in rollback_results:
            print(f"     - {result}")
        
        print("\n=== Example completed successfully ===")


if __name__ == "__main__":
    main()