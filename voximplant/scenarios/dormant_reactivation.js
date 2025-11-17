/**
 * LAYA Dormant User Reactivation Agent
 * VoxEngine Scenario for Voximplant
 *
 * Purpose: Re-engage users who became inactive in their digital wallet
 * Uses: Google Gemini Live API for Hebrew conversations
 */

require(Modules.Gemini);

// ============================================================================
// CONFIGURATION
// ============================================================================

const GEMINI_API_KEY = "YOUR_GEMINI_API_KEY";  // Replace with your actual key
const WEBHOOK_URL = "https://your-backend.com/webhook/voximplant";  // Replace with your backend URL

// Hebrew System Prompt for Dormant Reactivation
const SYSTEM_PROMPT = `
אתה נציג שירות לקוחות ידידותי ונעים של לייה - ארנק מט"ח דיגיטלי.

תפקידך: לשוב ולהפעיל משתמש שלא השתמש בחשבון שלו כבר זמן מה.

מידע על לייה:
- ארנק דיגיטלי רב-מטבעי עם כרטיס Mastercard
- 0% עמלת המרת מט"ח - חוסך המון כסף בנסיעות!
- כרטיס דיגיטלי + פיזי
- שימוש גם לקניות אונליין מחו"ל, לא רק נסיעות
- מוסדר ע"י רשות שוק ההון (רישיון 67037)

יעדים שלך:
1. להזכיר בעדינות את קיום החשבון ("ראינו שלא השתמשת כבר זמן מה")
2. לברר אם יש תוכניות נסיעה או קניות בינלאומיות בקרוב
3. להזכיר את הערך והחיסכון (הבנקים גוזרים 2-5% עמלה!)
4. להציע פעולה ספציפית: טעינת כסף, הזמנת כרטיס, או תזכורת לעתיד

טון השיחה: נעים, casual, ידידותי - לא פולשני. זו שיחה לבדיקת מצב, לא מכירה אגרסיבית.

שאלות מנחות:
- "יש תוכניות נסיעה לחו״ל בזמן הקרוב?"
- "קונה משהו מחו״ל באינטרנט לפעמים?"
- "איך היה החשבון בפעם האחרונה שהשתמשת?"
- "יש משהו שלא עבד טוב או שלא היה ברור?"

הצעות ערך:
- "זוכר שבלייה אין עמלות המרה? הבנק גוזר 2-5% בכל קניה בחו״ל"
- "אפשר להשתמש גם לקניות באמזון או אתרים זרים, לא רק נסיעות"
- "אם יש נסיעה מתוכננת, אפשר להכין עכשיו ככה זה מוכן וחלק"

הצעות פעולה:
- "רוצה שאעזור לך להטעין כסף עכשיו לקראת הנסיעה?"
- "אפשר להזמין גם כרטיס פיזי אם זה נוח לך יותר"
- "אשלח לך תזכורת לקראת עונת החופשות?"
- "יש לך חברים שנוסעים הרבה? תוכל לשלוח להם הפניה"

טיפול בתשובות שליליות:
📌 "אין לי תוכניות נסיעה"
→ "אני מבין. אם בעתיד יהיו תוכניות, החשבון שלך פעיל ומוכן. רוצה שאשלח לך תזכורת לקראת הקיץ?"

📌 "עברתי למתחרה / בנק אחר"
→ "בסדר גמור, מקווה שאתה מרוצה. סתם מעניין - האם יש שם גם 0% עמלות? אצלנו זה ללא עמלה כלל."

📌 "לא מעוניין / רוצה לסגור חשבון"
→ "הבנתי, תודה שהודעת. אם תרצה לסגור, אפשר לעשות את זה באפליקציה או שאני יכול לטפל בזה עבורך. מה נוח לך?"

📌 "היתה בעיה בשימוש הקודם"
→ "אני מצטער לשמוע. תוכל לספר מה קרה? אני ארשום ואדאג שזה יטופל."

הנחיות תקשורת:
- דבר בעברית טבעית וקלילה
- תן למשתמש להוביל - אל תהיה לחוץ
- אם הוא לא מעוניין - קבל את זה בנעימות
- הראה עניין אמיתי, לא רובוטי

בסוף השיחה - חובה:
קרא לפונקציה save_call_result עם:
- disposition: בחר את התוצאה המתאימה ביותר
- cx_score: דרג 1-10 את שביעות הרצון (לפי הטון, החוויה, האם עזרת)
- summary: סיכום קצר בעברית (2-3 משפטים)

אל תסיים את השיחה לפני שקראת לפונקציה!

דוגמאות לסיכום טוב:
- "הלקוח נוסע לפריז בעוד שבועיים, הבטיח להטעין כסף דרך האפליקציה מחר."
- "הלקוח עבר לבנק אחר, לא מעוניין לחזור."
- "אין תוכניות נסיעה כרגע, הסכים לקבל תזכורת לקראת הקיץ."
`;

// Function declarations
const TOOLS = [
  {
    functionDeclarations: [
      {
        name: "save_call_result",
        description: "Save the final outcome of the call - MUST be called at end of conversation",
        parameters: {
          type: "object",
          properties: {
            disposition: {
              type: "string",
              enum: [
                "REACTIVATED",              // User re-engaged, will use the service soon
                "REMINDED_VALUE",           // User appreciated reminder, may use later
                "NO_TRAVEL_PLANS",          // No immediate need/travel plans
                "FOUND_ALTERNATIVE",        // Switched to competitor/bank
                "NOT_INTERESTED"            // Wants to close account or not interested
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
      last_active: leadData.last_active || "unknown"
    };

    Logger.write(`👤 Calling: ${leadData.name} (${leadData.phone})`);
    Logger.write(`📅 Last active: ${leadData.last_active}`);

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
              voiceName: 'Kore'
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
      }
    });

    Logger.write("✅ Connected to Gemini Live API (Hebrew mode)");

    // Connect call audio with Gemini
    VoxEngine.sendMediaBetween(call, geminiClient);
    Logger.write("🔊 Audio bridge established: Call ↔ Gemini");

    // Listen for function calls
    geminiClient.addEventListener(Gemini.LiveAPIEvents.ToolCall, async (event) => {
      const functionCall = event.data;

      Logger.write("🔧 Function called by Gemini:");
      Logger.write(`   Name: ${functionCall.name}`);
      Logger.write(`   Parameters: ${JSON.stringify(functionCall.parameters, null, 2)}`);

      if (functionCall.name === "save_call_result") {
        const disposition = functionCall.parameters.disposition;
        const cx_score = functionCall.parameters.cx_score;
        const summary = functionCall.parameters.summary;

        Logger.write("💾 Saving call result...");

        // Send to backend
        await sendWebhook({
          type: "call_result",
          call_id: callData.call_id,
          lead_id: callData.lead_id,
          disposition: disposition,
          cx_score: cx_score,
          summary: summary
        });

        // Respond to Gemini
        geminiClient.sendToolResponse({
          id: functionCall.id,
          response: {
            success: true,
            message: "תוצאות השיחה נשמרו"
          }
        });

        Logger.write("✅ Call result saved");
        Logger.write(`   Disposition: ${disposition}`);
        Logger.write(`   CX Score: ${cx_score}/10`);

        // Hang up after goodbye
        setTimeout(() => {
          Logger.write("👋 Hanging up call");
          call.hangup();
        }, 4000);
      }
    });

    // Handle disconnection
    call.addEventListener(CallEvents.Disconnected, async () => {
      Logger.write("📴 Call disconnected");

      await sendWebhook({
        type: "call_ended",
        call_id: callData.call_id
      });

      if (geminiClient) {
        geminiClient.close();
      }

      VoxEngine.terminate();
    });

    // Handle failure
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
    Logger.write("❌ Error:");
    Logger.write(error.message);

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

async function sendWebhook(data) {
  try {
    await Net.httpRequestAsync(WEBHOOK_URL, {
      method: "POST",
      headers: ["Content-Type: application/json"],
      postData: JSON.stringify(data)
    });
    Logger.write(`📤 Webhook sent: ${data.type}`);
  } catch (error) {
    Logger.write(`⚠️  Webhook failed: ${error.message}`);
  }
}
