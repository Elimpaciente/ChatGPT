addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

const METADATA = {
  developer: 'El Impaciente',
  telegram_channel: 'https://t.me/Apisimpacientes'
}

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type'
}

const CONFIG = {
  url: "https://chatsandbox.com/api/chat",
  character: "openai-gpt-4o",
  maxRetries: 3,
  userAgents: [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
  ]
}

const getHeaders = () => ({
  "Content-Type": "application/json",
  "Accept": "*/*",
  "Accept-Language": "en-US,en;q=0.9",
  "User-Agent": CONFIG.userAgents[Math.floor(Math.random() * CONFIG.userAgents.length)],
  "Referer": `https://chatsandbox.com/chat/${CONFIG.character}`,
  "Origin": "https://chatsandbox.com"
})

async function handleRequest(request) {
  const url = new URL(request.url)
  
  if (!url.pathname.startsWith('/chat')) {
    return errorResponse('Endpoint not found. Use /chat', 404)
  }

  if (request.method !== 'GET') {
    return errorResponse('Only GET requests are allowed', 400)
  }

  const message = url.searchParams.get('message')?.trim()

  if (!message) {
    return errorResponse('The message parameter is required', 400)
  }

  try {
    const response = await getGPT4Response(message)
    return jsonResponse({ status_code: 200, ...METADATA, response }, 200, { 'Cache-Control': 'no-cache' })
  } catch (error) {
    return errorResponse(`Error connecting to service: ${error.message}`, 400)
  }
}

async function getGPT4Response(message) {
  let lastError = null

  for (let attempt = 0; attempt < CONFIG.maxRetries; attempt++) {
    try {
      if (attempt > 0) {
        await new Promise(resolve => setTimeout(resolve, 3000 + (attempt * 2000)))
      }

      const response = await fetch(CONFIG.url, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
          messages: [message],
          character: CONFIG.character
        }),
        signal: AbortSignal.timeout(60000)
      })

      if (response.status === 200) {
        const data = await response.text()
        const cleaned = data.trim()
        
        if (!cleaned) {
          lastError = new Error("Empty response")
          continue
        }
        
        return cleaned
      }

      if (response.status === 429 && attempt < CONFIG.maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, 10000 + (attempt * 5000)))
        continue
      }

      if (response.status === 403 && attempt < CONFIG.maxRetries - 1) {
        continue
      }

      lastError = new Error(`HTTP ${response.status}`)

    } catch (error) {
      lastError = error
      if (attempt < CONFIG.maxRetries - 1) continue
    }
  }

  throw lastError || new Error("Unknown error")
}

function errorResponse(message, status) {
  return jsonResponse({ status_code: status, ...METADATA, message }, status)
}

function jsonResponse(data, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: { 'Content-Type': 'application/json', ...CORS, ...extraHeaders }
  })
}
