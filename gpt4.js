addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

const CHATSANDBOX_URL = "https://chatsandbox.com/api/chat"
const CHATSANDBOX_CHARACTER = "openai-gpt-4o"

const USER_AGENTS = [
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

function getHeaders() {
  return {
    "Content-Type": "application/json",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)],
    "Referer": `https://chatsandbox.com/chat/${CHATSANDBOX_CHARACTER}`,
    "Origin": "https://chatsandbox.com"
  }
}

async function handleRequest(request) {
  const url = new URL(request.url)
  
  if (request.method !== 'GET') {
    return new Response(JSON.stringify({
      status_code: 400,
      developer: 'El Impaciente',
      telegram_channel: 'https://t.me/Apisimpacientes',
      message: 'Only GET requests are allowed'
    }), {
      status: 400,
      headers: { 
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    })
  }
  
  const message = url.searchParams.get('message')
  
  if (!message || message.trim() === '') {
    return new Response(JSON.stringify({
      status_code: 400,
      developer: 'El Impaciente',
      telegram_channel: 'https://t.me/Apisimpacientes',
      message: 'The message parameter is required'
    }), {
      status: 400,
      headers: { 
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    })
  }
  
  const maxRetries = 3
  let lastError = null
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      if (attempt > 0) {
        await new Promise(resolve => setTimeout(resolve, 3000 + (attempt * 2000)))
      }
      
      const response = await fetch(CHATSANDBOX_URL, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
          messages: [message],
          character: CHATSANDBOX_CHARACTER
        }),
        signal: AbortSignal.timeout(60000)
      })
      
      if (response.status === 200) {
        const data = await response.text()
        const cleanedData = data.trim()
        
        if (!cleanedData) {
          lastError = "Empty response"
          continue
        }
        
        return new Response(JSON.stringify({
          status_code: 200,
          developer: 'El Impaciente',
          telegram_channel: 'https://t.me/Apisimpacientes',
          response: cleanedData
        }), {
          status: 200,
          headers: { 
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'
          }
        })
      }
      
      if (response.status === 429) {
        if (attempt < maxRetries - 1) {
          await new Promise(resolve => setTimeout(resolve, 10000 + (attempt * 5000)))
          continue
        }
      }
      
      if (response.status === 403 && attempt < maxRetries - 1) {
        continue
      }
      
      lastError = `HTTP ${response.status}`
      
    } catch (error) {
      lastError = error.message
      if (attempt < maxRetries - 1) {
        continue
      }
    }
  }
  
  return new Response(JSON.stringify({
    status_code: 400,
    developer: 'El Impaciente',
    telegram_channel: 'https://t.me/Apisimpacientes',
    message: `Error connecting to service: ${lastError}`
  }), {
    status: 400,
    headers: { 
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*'
    }
  })
}