/**
 * LAYA Registration Recovery Agent
 * VoxEngine Scenario for Voximplant
 *
 * Purpose: Re-engage users who dropped off during registration
 * Uses: Google Gemini Live API for Hebrew conversations
 */

require(Modules.Gemini);

// ============================================================================
// CONFIGURATION
// ============================================================================

const GEMINI_API_KEY = "YOUR_GEMINI_API_KEY";  // Replace with your actual key
const WEBHOOK_URL = "https://your-backend.com/webhook/voximplant";  // Replace with your backend URL

// Hebrew System Prompt for Registration Recovery
const SYSTEM_PROMPT = `
אתה נציג שירות לקוחות ידידותי ומקצועי של לייה - ארנק מט"ח דיגיטלי.

תפקידך: לעזור למשתמש להשלים הרשמה שהוא התחיל אבל לא סיים.

מידע על לייה:
- ארנק דיגיטלי רב-מטבעי עם כרטיס Mastercard
- 0% עמלת המרת מט"ח (זה היתרון המרכזי!)
- כרטיס דיגיטלי מוכן תוך 2 דקות, בחינם
- מוסדר ע"י רשות שוק ההון הישראלית (רישיון 67037)

יעדים שלך:
1. לברר בעדינות מדוע המשתמש עצר בתהליך (בעיה טכנית? חשש? לא הבין?)
2. לטפל בהתנגדויות בסבלנות ואמפתיה
3. להזכיר את הערך: חיסכון אמיתי בעמלות, נוחות, אבטחה
4. להוביל להשלמת ההרשמה - עכשיו או בזמן מוסכם ספציפי

טון השיחה: חם, אמפתי, מועיל - לא לוחץ ולא אגרסיבי. אתה כאן לעזור, לא למכור.

התנגדויות נפוצות ואיך לטפל בהן:

📌 "אני מודאג מפרטיות / אבטחה"
→ "מובן לחלוטין, זה חשוב מאוד. לייה מוסדרת ע״י רשות שוק ההון הישראלית ברישיון 67037, והנתונים שלך מאובטחים לפי תקן בנקאי. הכל מוגן ומוצפן."

📌 "זה נראה מסובך"
→ "אני כאן בדיוק בשביל זה! אני יכול ללוות אותך צעד אחר צעד. התהליך ממש פשוט ולוקח רק 2 דקות. מה לא ברור לך?"

📌 "אין לי נסיעה מתוכננת עכשיו"
→ "זה בעצם הזמן המושלם להתכונן! ככה כשתצא לנסיעה הבאה הכל כבר יהיה מוכן וחלק. בנוסף, אפשר להשתמש גם לקניות אונליין מחו״ל."

📌 "אין לי זמן עכשיו"
→ "אני מבין. זה לוקח רק 2 דקות, אבל אם אתה ממש לא יכול עכשיו - מתי יהיה לך נוח? אשמח לשלוח לך SMS עם לינק ישיר."

📌 "נתקלתי בבעיה טכנית"
→ "אני מצטער לשמוע. תוכל לספר לי איזו בעיה? אני ארשום את זה ואדאג שהמחלקה הטכנית תצור איתך קשר תוך 24 שעות לפתור את זה."

הנחיות תקשורת:
- דבר בעברית טבעית וברורה
- השתמש במשפטים קצרים ופשוטים
- תן למשתמש לדבר - הקשב ואל תקטע
- הראה אמפתיה והבנה
- אל תהיה לחוץ או אגרסיבי

בסוף השיחה - חובה:
קרא לפונקציה save_call_result עם:
- disposition: בחר את התוצאה המתאימה ביותר מהרשימה
- cx_score: דרג 1-10 את שביעות הרצון של הלקוח (לפי הטון שלו, האם עזרת, האם היה מרוצה)
- summary: סיכום קצר בעברית (2-3 משפטים) של מה קרה בשיחה

אל תסיים את השיחה לפני שקראת לפונקציה!

דוגמאות לסיכום טוב:
- "הלקוח היה מודאג מאבטחה, הסברתי על הרגולציה והוא הסכים להשלים מחר בבוקר."
- "בעיה טכנית בהעלאת תעודה מזהה. הבטחתי שהמחלקה הטכנית תיצור קשר תוך 24 שעות."
- "הלקוח לא מעוניין כרגע, אין לו תוכניות נסיעה."
`;

// Function declarations for Gemini
const TOOLS = [
  {
    functionDeclarations: [
      {
        name: "save_call_result",
        description: "Save the final outcome of the call - MUST be called at the end of every conversation",
        parameters: {
          type: "object",
          properties: {
            disposition: {
              type: "string",
              enum: [
                "COMPLETED_REGISTRATION",      // User agreed to complete registration now
                "SCHEDULED_COMPLETION",        // User committed to complete at specific time
                "NEEDS_HELP",                  // Technical issue, needs human follow-up
                "NOT_INTERESTED",              // Explicitly declined, not interested
                "WRONG_NUMBER"                 // Wrong contact information
              ],
              description: "The final outcome/result of the call"
            },
            cx_score: {
              type: "integer",
              minimum: 1,
              maximum: 10,
              description: "Customer satisfaction score from 1 (very dissatisfied) to 10 (very satisfied)"
            },
            summary: {
              type: "string",
              description: "Brief Hebrew summary of what happened in the call (2-3 sentences)"
            }
          },
          required: ["disposition", "cx_score", "summary"]
        }
      }
    ]
  }
];

// ============================================================================
// MAIN EVENT HANDLER
// ============================================================================

VoxEngine.addEventListener(AppEvents.CallAlerting, async ({ call }) => {
  let geminiClient = null;
  let callData = {};

  try {
    // Answer the call
    call.answer();
    Logger.write("📞 Call answered");

    // Get lead data from custom data
    const leadData = JSON.parse(call.customData());
    callData = {
      call_id: leadData.call_id,
      lead_id: leadData.lead_id,
      lead_name: leadData.name,
      lead_type: leadData.type,
      drop_stage: leadData.drop_stage || "unknown"
    };

    Logger.write(`👤 Calling: ${leadData.name} (${leadData.phone})`);
    Logger.write(`📍 Drop stage: ${leadData.drop_stage}`);

    // Notify backend: call started
    await sendWebhook({
      type: "call_started",
      call_id: callData.call_id,
      lead_id: callData.lead_id,
      lead_name: callData.lead_name,
      lead_type: callData.lead_type,
      voximplant_call_id: call.id(),
      timestamp: new Date().toISOString()
    });

    // Create Gemini Live API Client
    Logger.write("🤖 Initializing Gemini Live API...");

    geminiClient = await Gemini.createLiveAPIClient({
      apiKey: GEMINI_API_KEY,
      model: 'gemini-2.0-flash-exp',
      connectConfig: {
        responseModalities: ["AUDIO"],
        speechConfig: {
          languageCode: 'he-IL',  // Hebrew (Israel)
          voiceConfig: {
            prebuiltVoiceConfig: {
              voiceName: 'Kore'  // Choose appropriate voice
            }
          }
        },
        systemInstruction: {
          parts: [{ text: SYSTEM_PROMPT }]
        },
        tools: TOOLS
      },
      onWebSocketClose: (evt) => {
        Logger.write("🔌 Gemini WebSocket closed");
        Logger.write(JSON.stringify(evt));
      }
    });

    Logger.write("✅ Connected to Gemini Live API (Hebrew mode)");

    // Connect call audio bidirectionally with Gemini
    // This is the magic - audio flows directly between caller and Gemini!
    VoxEngine.sendMediaBetween(call, geminiClient);
    Logger.write("🔊 Audio bridge established: Call ↔ Gemini");

    // Listen for function calls from Gemini
    geminiClient.addEventListener(Gemini.LiveAPIEvents.ToolCall, async (event) => {
      const functionCall = event.data;

      Logger.write("🔧 Function called by Gemini:");
      Logger.write(`   Name: ${functionCall.name}`);
      Logger.write(`   Parameters: ${JSON.stringify(functionCall.parameters, null, 2)}`);

      if (functionCall.name === "save_call_result") {
        // Extract result data
        const disposition = functionCall.parameters.disposition;
        const cx_score = functionCall.parameters.cx_score;
        const summary = functionCall.parameters.summary;

        Logger.write("💾 Saving call result...");

        // Send result to backend
        await sendWebhook({
          type: "call_result",
          call_id: callData.call_id,
          lead_id: callData.lead_id,
          disposition: disposition,
          cx_score: cx_score,
          summary: summary
        });

        // Respond to Gemini that function executed successfully
        geminiClient.sendToolResponse({
          id: functionCall.id,
          response: {
            success: true,
            message: "תוצאות השיחה נשמרו בהצלחה"
          }
        });

        Logger.write("✅ Call result saved successfully");
        Logger.write(`   Disposition: ${disposition}`);
        Logger.write(`   CX Score: ${cx_score}/10`);
        Logger.write(`   Summary: ${summary}`);

        // Give Gemini time to say goodbye politely, then hang up
        setTimeout(() => {
          Logger.write("👋 Hanging up call");
          call.hangup();
        }, 4000);  // 4 seconds for goodbye
      }
    });

    // Handle call disconnection
    call.addEventListener(CallEvents.Disconnected, async () => {
      Logger.write("📴 Call disconnected");

      // Notify backend
      await sendWebhook({
        type: "call_ended",
        call_id: callData.call_id
      });

      // Close Gemini connection
      if (geminiClient) {
        geminiClient.close();
      }

      VoxEngine.terminate();
    });

    // Handle call failure
    call.addEventListener(CallEvents.Failed, async () => {
      Logger.write("❌ Call failed");

      await sendWebhook({
        type: "call_ended",
        call_id: callData.call_id
      });

      if (geminiClient) {
        geminiClient.close();
      }

      VoxEngine.terminate();
    });

  } catch (error) {
    Logger.write("❌ Error in scenario:");
    Logger.write(error.message);
    Logger.write(error.stack);

    // Notify backend of error
    await sendWebhook({
      type: "call_error",
      call_id: callData.call_id,
      error: error.message
    });

    if (call) {
      call.hangup();
    }
    VoxEngine.terminate();
  }
});

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Send webhook to backend
 */
async function sendWebhook(data) {
  try {
    const response = await Net.httpRequestAsync(WEBHOOK_URL, {
      method: "POST",
      headers: ["Content-Type: application/json"],
      postData: JSON.stringify(data)
    });

    Logger.write(`📤 Webhook sent: ${data.type}`);
    return response;
  } catch (error) {
    Logger.write(`⚠️  Failed to send webhook: ${error.message}`);
  }
}
