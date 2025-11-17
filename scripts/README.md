# 🤖 Voximplant Automation Scripts

Automated setup scripts for deploying VoxEngine scenarios via API.

---

## 📄 `setup_voximplant.py`

Automatically creates/updates Voximplant scenarios and routing rules via API, eliminating the need for manual UI configuration.

### What It Does:

1. ✅ Creates or retrieves "LAYA Calling Agent" application
2. ✅ Uploads/updates VoxEngine scenarios from `/voximplant/scenarios/`
3. ✅ Replaces placeholders with actual API keys and URLs
4. ✅ Creates routing rules and links them to scenarios
5. ✅ Returns Rule IDs for your `.env` configuration

### Prerequisites:

Before running the script, you need:

- [ ] **Voximplant account** - Sign up at [voximplant.com](https://voximplant.com)
- [ ] **Account ID** - Found in Voximplant dashboard under Settings
- [ ] **API Key** - Create in Settings → API → Create API Key
- [ ] **Gemini API Key** - Get from [Google AI Studio](https://aistudio.google.com/app/apikey)

### Setup:

1. **Install Python dependencies:**
   ```bash
   cd /path/to/Laya
   source backend/venv/bin/activate
   pip install voximplant-apiclient python-dotenv
   ```

2. **Update backend/.env with real credentials:**
   ```bash
   # Replace these placeholder values:
   VOXIMPLANT_ACCOUNT_ID=your_actual_account_id
   VOXIMPLANT_API_KEY=your_actual_api_key
   GEMINI_API_KEY=your_actual_gemini_key
   BACKEND_URL=http://localhost:8000  # Or production URL
   ```

### Usage:

```bash
# Make sure you're in the Laya project root directory
cd /path/to/Laya

# Run the setup script
python scripts/setup_voximplant.py
```

### Expected Output:

```
============================================================
🚀 Voximplant Automated Setup
============================================================
✅ Initialized Voximplant API client
   Account ID: your_account_id

✅ Found application: LAYA Calling Agent (ID: 12345)

📄 Processing scenario: registration_recovery
   Found existing scenario (ID: 67890)
✅ Updated scenario: registration_recovery

📄 Processing scenario: dormant_reactivation
✅ Created scenario: dormant_reactivation (ID: 67891)

🔀 Processing rule: registration_recovery_rule
✅ Created rule: registration_recovery_rule (ID: 111222)

🔀 Processing rule: dormant_reactivation_rule
✅ Created rule: dormant_reactivation_rule (ID: 111223)

============================================================
✅ Setup Complete!
============================================================

Application ID: 12345

Scenarios:
  - registration_recovery: 67890
  - dormant_reactivation: 67891

Routing Rules (USE THESE IN .env):
  - Registration Rule ID: 111222
  - Dormant Rule ID: 111223

📝 Update your backend/.env file:
VOXIMPLANT_SCENARIO_ID_REGISTRATION=111222
VOXIMPLANT_SCENARIO_ID_DORMANT=111223

============================================================
✨ All done! Your Voximplant is configured and ready to go!
```

### Next Steps:

After running the script:

1. **Copy the Rule IDs** from the output
2. **Update `backend/.env`:**
   ```bash
   VOXIMPLANT_SCENARIO_ID_REGISTRATION=111222
   VOXIMPLANT_SCENARIO_ID_DORMANT=111223
   ```
3. **Restart your backend** for changes to take effect
4. **Test a call** from the frontend UI

---

## 🔄 Updating Scenarios

If you modify the VoxEngine scenarios in `/voximplant/scenarios/`, simply run the script again:

```bash
python scripts/setup_voximplant.py
```

The script will:
- ✅ Detect existing scenarios by name
- ✅ Update them with new code
- ✅ Keep the same IDs (no need to update .env again)

---

## 🐛 Troubleshooting

### Error: "Missing VOXIMPLANT_ACCOUNT_ID or VOXIMPLANT_API_KEY"

**Solution:** Make sure `backend/.env` has valid credentials:
```bash
VOXIMPLANT_ACCOUNT_ID=your_account_id
VOXIMPLANT_API_KEY=your_api_key
```

### Warning: "GEMINI_API_KEY not set"

The script will continue but scenarios will have a placeholder key. Options:
- Press `y` to continue (you can update the key later in Voximplant UI)
- Press `n` to abort and set the key in `.env` first

### Error: API authentication failed

**Causes:**
- Invalid Account ID format (should be a number)
- Wrong API Key
- API Key doesn't have sufficient permissions

**Solution:**
1. Verify credentials in Voximplant dashboard
2. Regenerate API Key if needed
3. Ensure API Key has "Scenario management" permissions

### Script creates duplicates

The script checks for existing scenarios/rules by **name**. If you rename scenarios, it will create new ones.

**Solution:** Delete old scenarios manually in Voximplant UI, or keep consistent naming.

---

## 📚 API Reference

The script uses the official Voximplant Python SDK:
- [API Documentation](https://voximplant.com/docs/references/httpapi/)
- [Python SDK](https://github.com/voximplant/apiclient-python)

### Key API Methods Used:

```python
# Get applications
api.get_applications()

# Create application
api.add_application(application_name="...")

# Create scenario
api.add_scenario(
    scenario_name="...",
    scenario_script="..."
)

# Update scenario
api.set_scenario_info(
    scenario_id=123,
    scenario_script="..."
)

# Create routing rule
api.add_rule(
    application_id=123,
    rule_name="...",
    rule_pattern=".*",
    scenario_id=456
)
```

---

## 🔐 Security Notes

- ⚠️ Never commit `.env` file to git (already in `.gitignore`)
- ⚠️ API keys have full account access - keep them secure
- ⚠️ The script reads API keys from `.env` only
- ✅ All API communication uses HTTPS

---

## ✅ Benefits of Automation

**Without automation (manual UI):**
- ❌ Copy/paste scenarios manually
- ❌ Find/replace placeholders by hand
- ❌ Navigate multiple UI screens
- ❌ Manually copy IDs
- ❌ Risk of human error

**With automation (this script):**
- ✅ One command deployment
- ✅ Automatic placeholder replacement
- ✅ Idempotent (safe to run multiple times)
- ✅ Version controlled scenario code
- ✅ Easy updates and rollbacks

---

## 📞 Support

For issues with:
- **Script itself**: Check error messages and troubleshooting above
- **Voximplant API**: See [Voximplant Documentation](https://voximplant.com/docs/)
- **Account setup**: Contact Voximplant support

---

**Built for LAYA Calling Agent** 🚀
