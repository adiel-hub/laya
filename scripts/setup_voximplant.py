#!/usr/bin/env python3
"""
Voximplant Setup Script
Automatically creates/updates scenarios and routing rules via HTTP API
"""

import os
import sys
import json
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

# Configuration
ACCOUNT_ID = os.getenv('VOXIMPLANT_ACCOUNT_ID')
API_KEY = os.getenv('VOXIMPLANT_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
WEBHOOK_URL = os.getenv('BACKEND_URL', 'http://localhost:8000') + '/webhook/voximplant'

# Voximplant API endpoint
API_BASE_URL = 'https://api.voximplant.com/platform_api'

# Paths to scenario files
SCENARIOS_DIR = Path(__file__).parent.parent / 'voximplant' / 'scenarios'
REGISTRATION_SCENARIO_FILE = SCENARIOS_DIR / 'registration_recovery.js'
DORMANT_SCENARIO_FILE = SCENARIOS_DIR / 'dormant_reactivation.js'


class VoximplantSetup:
    """Handle Voximplant setup via HTTP API"""

    def __init__(self):
        if not ACCOUNT_ID or not API_KEY:
            raise ValueError("Missing VOXIMPLANT_ACCOUNT_ID or VOXIMPLANT_API_KEY in .env")

        self.account_id = ACCOUNT_ID
        self.api_key = API_KEY
        self.application_id = None

        print(f"✅ Initialized Voximplant API client")
        print(f"   Account ID: {ACCOUNT_ID}")

    def _make_request(self, method, params=None):
        """Make HTTP request to Voximplant API"""
        if params is None:
            params = {}

        params['account_id'] = self.account_id
        params['api_key'] = self.api_key

        try:
            response = requests.post(f"{API_BASE_URL}/{method}", data=params)
            response.raise_for_status()
            result = response.json()

            if 'error' in result:
                raise Exception(f"API Error: {result['error']}")

            return result
        except requests.exceptions.RequestException as e:
            raise Exception(f"HTTP Request failed: {e}")

    def get_or_create_application(self, app_name="laya"):
        """Get or create application"""
        try:
            # Get applications
            result = self._make_request('GetApplications')

            # Check if app exists
            apps = result.get('result', [])
            if isinstance(apps, list):
                for app in apps:
                    app_full_name = app.get('application_name', '')
                    # Match either exact name or name prefix (before .domain)
                    if app_full_name == app_name or app_full_name.startswith(f"{app_name}."):
                        self.application_id = app['application_id']
                        print(f"✅ Found application: {app_full_name} (ID: {self.application_id})")
                        return self.application_id

            # Create new application
            print(f"📝 Creating new application: {app_name}")
            try:
                result = self._make_request('AddApplication', {
                    'application_name': app_name
                })
                self.application_id = result['result']
                print(f"✅ Created application (ID: {self.application_id})")
                return self.application_id
            except Exception as create_error:
                # If creation fails because name exists, try to find it again
                if 'not unique' in str(create_error).lower():
                    # Application was created between checks, fetch again
                    result = self._make_request('GetApplications')
                    apps = result.get('result', [])
                    if isinstance(apps, list):
                        for app in apps:
                            app_full_name = app.get('application_name', '')
                            if app_full_name == app_name or app_full_name.startswith(f"{app_name}."):
                                self.application_id = app['application_id']
                                print(f"✅ Found application: {app_full_name} (ID: {self.application_id})")
                                return self.application_id
                raise

        except Exception as e:
            print(f"❌ Error with application: {e}")
            raise

    def read_scenario_file(self, file_path):
        """Read and prepare scenario file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Replace placeholders
        content = content.replace('YOUR_GEMINI_API_KEY', GEMINI_API_KEY or 'REPLACE_WITH_REAL_KEY')
        content = content.replace('https://your-backend.com/webhook/voximplant', WEBHOOK_URL)

        return content

    def create_or_update_scenario(self, scenario_name, scenario_file):
        """Create or update scenario"""
        try:
            # Read scenario content
            print(f"\n📄 Processing scenario: {scenario_name}")
            scenario_script = self.read_scenario_file(scenario_file)

            # Check if scenario exists
            result = self._make_request('GetScenarios')
            scenario_id = None

            for scenario in result.get('result', []):
                if scenario['scenario_name'] == scenario_name:
                    scenario_id = scenario['scenario_id']
                    print(f"   Found existing scenario (ID: {scenario_id})")
                    break

            if scenario_id:
                # Update existing scenario
                self._make_request('SetScenarioInfo', {
                    'scenario_id': scenario_id,
                    'scenario_name': scenario_name,
                    'scenario_script': scenario_script
                })
                print(f"✅ Updated scenario: {scenario_name}")
            else:
                # Create new scenario
                result = self._make_request('AddScenario', {
                    'scenario_name': scenario_name,
                    'scenario_script': scenario_script
                })
                scenario_id = result['result']
                print(f"✅ Created scenario: {scenario_name} (ID: {scenario_id})")

            return scenario_id

        except Exception as e:
            print(f"❌ Error with scenario {scenario_name}: {e}")
            raise

    def create_or_update_rule(self, rule_name, scenario_id, rule_pattern=".*"):
        """Create or update routing rule"""
        try:
            print(f"\n🔀 Processing rule: {rule_name}")

            # Check if rule exists
            result = self._make_request('GetRules', {
                'application_id': int(self.application_id)
            })
            rule_id = None

            for rule in result.get('result', []):
                if rule['rule_name'] == rule_name:
                    rule_id = rule['rule_id']
                    print(f"   Found existing rule (ID: {rule_id})")
                    break

            if rule_id:
                # Update existing rule
                self._make_request('SetRuleInfo', {
                    'rule_id': rule_id,
                    'rule_name': rule_name,
                    'rule_pattern': rule_pattern,
                    'scenarios': scenario_id
                })
                print(f"✅ Updated rule: {rule_name}")
            else:
                # Create new rule
                result = self._make_request('AddRule', {
                    'application_id': int(self.application_id),
                    'rule_name': rule_name,
                    'rule_pattern': rule_pattern,
                    'scenarios': scenario_id
                })
                rule_id = result['result']
                print(f"✅ Created rule: {rule_name} (ID: {rule_id})")

            return rule_id

        except Exception as e:
            print(f"❌ Error with rule {rule_name}: {e}")
            raise

    def setup_all(self):
        """Setup everything"""
        print("\n" + "="*60)
        print("🚀 Voximplant Automated Setup")
        print("="*60)

        # Step 1: Create/get application
        self.get_or_create_application()

        # Step 2: Create/update scenarios
        dropoff_scenario_id = self.create_or_update_scenario(
            'dropoff',
            REGISTRATION_SCENARIO_FILE
        )

        dormant_scenario_id = self.create_or_update_scenario(
            'dormant',
            DORMANT_SCENARIO_FILE
        )

        # Step 3: Create/update routing rules
        dropoff_rule_id = self.create_or_update_rule(
            'dropoff_rule',
            dropoff_scenario_id
        )

        dormant_rule_id = self.create_or_update_rule(
            'dormant_rule',
            dormant_scenario_id
        )

        # Print summary
        print("\n" + "="*60)
        print("✅ Setup Complete!")
        print("="*60)
        print(f"\nApplication ID: {self.application_id}")
        print(f"\nScenarios:")
        print(f"  - dropoff: {dropoff_scenario_id}")
        print(f"  - dormant: {dormant_scenario_id}")
        print(f"\nRouting Rules (USE THESE IN .env):")
        print(f"  - Dropoff Rule ID: {dropoff_rule_id}")
        print(f"  - Dormant Rule ID: {dormant_rule_id}")

        print(f"\n📝 Update your backend/.env file:")
        print(f"VOXIMPLANT_SCENARIO_ID_REGISTRATION={dropoff_rule_id}")
        print(f"VOXIMPLANT_SCENARIO_ID_DORMANT={dormant_rule_id}")

        print("\n" + "="*60)

        return {
            'application_id': self.application_id,
            'scenarios': {
                'dropoff': dropoff_scenario_id,
                'dormant': dormant_scenario_id
            },
            'rules': {
                'dropoff': dropoff_rule_id,
                'dormant': dormant_rule_id
            }
        }


def main():
    """Main function"""
    try:
        # Check if Gemini API key is set
        if not GEMINI_API_KEY or GEMINI_API_KEY == 'test_gemini_key':
            print("\n⚠️  WARNING: GEMINI_API_KEY not set in .env")
            print("   Scenarios will be created with placeholder key")
            print("   You'll need to update them manually or re-run after setting the key\n")

        # Run setup
        setup = VoximplantSetup()
        result = setup.setup_all()

        print("\n✨ All done! Your Voximplant is configured and ready to go!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
