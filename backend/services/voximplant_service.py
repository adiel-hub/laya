"""
Voximplant Service - Integration with Voximplant API
"""

from voximplant.apiclient import VoximplantAPI, VoximplantException
import json
import os
from typing import Optional
from database.models import Lead


class VoximplantService:
    """Service class for Voximplant API integration"""

    def __init__(self):
        """Initialize Voximplant API client"""
        self.account_id = os.getenv("VOXIMPLANT_ACCOUNT_ID")
        self.api_key = os.getenv("VOXIMPLANT_API_KEY")

        if not self.account_id or not self.api_key:
            raise ValueError("Voximplant credentials not configured in environment variables")

        # Initialize API client
        # Note: The Python SDK uses account credentials format
        self.api = VoximplantAPI(f"{self.account_id}.json", self.api_key)

        # Scenario IDs for different call types
        self.scenario_id_registration = os.getenv("VOXIMPLANT_SCENARIO_ID_REGISTRATION")
        self.scenario_id_dormant = os.getenv("VOXIMPLANT_SCENARIO_ID_DORMANT")

    def trigger_call(self, lead: Lead, call_id: str) -> dict:
        """
        Trigger an outbound call via Voximplant

        Args:
            lead: Lead object to call
            call_id: Internal call ID (UUID)

        Returns:
            Dictionary with result information

        Raises:
            VoximplantException: If API call fails
        """
        # Select appropriate scenario based on lead type
        if lead.type == "drop-off":
            scenario_id = self.scenario_id_registration
        elif lead.type == "dormant":
            scenario_id = self.scenario_id_dormant
        else:
            raise ValueError(f"Unknown lead type: {lead.type}")

        # Prepare custom data to pass to VoxEngine scenario
        custom_data = {
            "call_id": call_id,  # Our internal call ID
            "lead_id": lead.id,
            "name": lead.name,
            "type": lead.type,
            "drop_stage": lead.drop_stage or "",
            "last_active": str(lead.last_active) if lead.last_active else ""
        }

        try:
            # Start the scenario
            # Note: Adjust parameters based on your Voximplant setup
            result = self.api.start_scenarios(
                rule_id=int(scenario_id),
                script_custom_data=json.dumps(custom_data),
                user={"phone": lead.phone}  # Target phone number
            )

            return {
                "success": True,
                "voximplant_result": result,
                "call_id": call_id
            }

        except VoximplantException as e:
            return {
                "success": False,
                "error": str(e),
                "call_id": call_id
            }

    def get_call_history(self, call_session_history_id: int) -> Optional[dict]:
        """
        Get call history from Voximplant

        Args:
            call_session_history_id: Voximplant call session history ID

        Returns:
            Dictionary with call history or None if not found
        """
        try:
            result = self.api.get_call_history(
                call_session_history_id=call_session_history_id
            )
            return result
        except VoximplantException as e:
            print(f"Error fetching call history: {e}")
            return None

    def get_account_info(self) -> Optional[dict]:
        """
        Get Voximplant account information (for testing/debugging)

        Returns:
            Dictionary with account info or None if error
        """
        try:
            result = self.api.get_account_info()
            return result
        except VoximplantException as e:
            print(f"Error fetching account info: {e}")
            return None
