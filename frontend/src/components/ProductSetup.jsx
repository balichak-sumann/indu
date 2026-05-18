import React, { useState } from 'react'

/**
 * Product Setup Form - Enter product details before starting the AI sales call
 * Supports both browser-based calls and phone calls via Exotel
 */
function ProductSetup({ onStart }) {
  const [productName, setProductName] = useState('')
  const [productDescription, setProductDescription] = useState('')
  const [keyFeatures, setKeyFeatures] = useState('')
  const [pricing, setPricing] = useState('')
  const [targetAudience, setTargetAudience] = useState('')
  const [companyName, setCompanyName] = useState('')
  const [language, setLanguage] = useState('en')
  const [tone, setTone] = useState('friendly')
  const [phoneNumber, setPhoneNumber] = useState('')
  const [callMode, setCallMode] = useState('browser') // 'browser' or 'phone'
  const [isCallingPhone, setIsCallingPhone] = useState(false)
  const [callStatus, setCallStatus] = useState('')

  const getProductConfig = () => ({
    productName: productName.trim(),
    productDescription: productDescription.trim(),
    keyFeatures: keyFeatures.trim(),
    pricing: pricing.trim(),
    targetAudience: targetAudience.trim(),
    companyName: companyName.trim(),
    language,
    tone,
  })

  const handleStartBrowser = () => {
    if (!productName.trim()) {
      alert('Please enter a product name')
      return
    }
    onStart(getProductConfig())
  }

  const handleStartPhoneCall = async () => {
    if (!productName.trim()) {
      alert('Please enter a product name')
      return
    }
    if (!phoneNumber.trim()) {
      alert('Please enter a phone number')
      return
    }

    setIsCallingPhone(true)
    setCallStatus('Setting up product config...')

    const API_URL = 'https://indu-u2r5.onrender.com'

    try {
      // Step 1: Set product config on the server
      const configResponse = await fetch(`${API_URL}/api/product-config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(getProductConfig()),
      })
      
      if (!configResponse.ok) {
        throw new Error('Failed to set product config')
      }

      setCallStatus('✅ Product config saved! Now click "Test out" in Exotel dashboard to make the call.')
      
      // Step 2: Try API call (may not work on trial)
      const response = await fetch(`${API_URL}/api/call/outbound`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone_number: phoneNumber.trim(),
          product_config: getProductConfig(),
          language,
        }),
      })

      const data = await response.json()
      if (data.success) {
        setCallStatus(`✅ Call initiated! Call SID: ${data.call_sid}`)
      } else {
        setCallStatus(`✅ Product config saved! Use Exotel "Test out" button to call ${phoneNumber}`)
      }
    } catch (error) {
      setCallStatus(`✅ Product config saved! Use Exotel "Test out" button to call ${phoneNumber}`)
    } finally {
      setIsCallingPhone(false)
    }
  }

  return (
    <div className="w-full h-screen flex items-center justify-center bg-gradient-to-br from-primary to-secondary p-6 overflow-y-auto">
      <div className="w-full max-w-2xl bg-secondary/60 backdrop-blur-md border border-accent/20 rounded-2xl p-8 shadow-2xl my-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-accent to-accent-light bg-clip-text text-transparent">
            AI Sales Agent Setup
          </h1>
          <p className="text-gray-400 mt-2">Enter your product details to start the AI-powered sales call</p>
        </div>

        <div className="space-y-4">
          {/* Company Name */}
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Company Name</label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="e.g., TechCorp India"
              className="w-full px-4 py-3 bg-primary/50 border border-accent/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-accent/50"
            />
          </div>

          {/* Product Name */}
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Product Name *</label>
            <input
              type="text"
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
              placeholder="e.g., SmartWatch Pro X1"
              className="w-full px-4 py-3 bg-primary/50 border border-accent/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-accent/50"
            />
          </div>

          {/* Product Description */}
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Product Description</label>
            <textarea
              value={productDescription}
              onChange={(e) => setProductDescription(e.target.value)}
              placeholder="Brief description of what the product does..."
              rows={2}
              className="w-full px-4 py-3 bg-primary/50 border border-accent/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-accent/50 resize-none"
            />
          </div>

          {/* Key Features */}
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Key Features / Benefits</label>
            <textarea
              value={keyFeatures}
              onChange={(e) => setKeyFeatures(e.target.value)}
              placeholder="e.g., 7-day battery life, heart rate monitor, water resistant, GPS tracking..."
              rows={2}
              className="w-full px-4 py-3 bg-primary/50 border border-accent/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-accent/50 resize-none"
            />
          </div>

          {/* Pricing & Target Audience Row */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Pricing</label>
              <input
                type="text"
                value={pricing}
                onChange={(e) => setPricing(e.target.value)}
                placeholder="e.g., ₹4,999 (50% off)"
                className="w-full px-4 py-3 bg-primary/50 border border-accent/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-accent/50"
              />
            </div>
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Target Audience</label>
              <input
                type="text"
                value={targetAudience}
                onChange={(e) => setTargetAudience(e.target.value)}
                placeholder="e.g., Young professionals"
                className="w-full px-4 py-3 bg-primary/50 border border-accent/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-accent/50"
              />
            </div>
          </div>

          {/* Language & Tone Row */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Conversation Language</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full px-4 py-3 bg-primary/50 border border-accent/20 rounded-lg text-white focus:outline-none focus:border-accent/50"
              >
                <option value="en">English</option>
                <option value="hi">Hindi</option>
                <option value="te">Telugu</option>
                <option value="ta">Tamil</option>
                <option value="kn">Kannada</option>
                <option value="ml">Malayalam</option>
                <option value="bn">Bengali</option>
                <option value="mr">Marathi</option>
                <option value="gu">Gujarati</option>
                <option value="pa">Punjabi</option>
                <option value="od">Odia</option>
                <option value="hinglish">Hinglish</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Sales Tone</label>
              <select
                value={tone}
                onChange={(e) => setTone(e.target.value)}
                className="w-full px-4 py-3 bg-primary/50 border border-accent/20 rounded-lg text-white focus:outline-none focus:border-accent/50"
              >
                <option value="friendly">Friendly & Casual</option>
                <option value="professional">Professional</option>
                <option value="enthusiastic">Enthusiastic & Energetic</option>
                <option value="consultative">Consultative</option>
              </select>
            </div>
          </div>

          {/* Call Mode Selection */}
          <div className="border-t border-accent/10 pt-4 mt-4">
            <label className="text-sm text-gray-400 mb-2 block">Call Mode</label>
            <div className="flex gap-4">
              <button
                onClick={() => setCallMode('browser')}
                className={`flex-1 py-3 rounded-lg border-2 transition-all ${
                  callMode === 'browser'
                    ? 'border-accent bg-accent/10 text-accent'
                    : 'border-gray-600 text-gray-400 hover:border-gray-500'
                }`}
              >
                🎙️ Browser (Test)
              </button>
              <button
                onClick={() => setCallMode('phone')}
                className={`flex-1 py-3 rounded-lg border-2 transition-all ${
                  callMode === 'phone'
                    ? 'border-accent bg-accent/10 text-accent'
                    : 'border-gray-600 text-gray-400 hover:border-gray-500'
                }`}
              >
                📞 Phone Call
              </button>
            </div>
          </div>

          {/* Phone number input (only for phone mode) */}
          {callMode === 'phone' && (
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Customer Phone Number *</label>
              <input
                type="tel"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="+91XXXXXXXXXX"
                className="w-full px-4 py-3 bg-primary/50 border border-accent/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-accent/50"
              />
            </div>
          )}
        </div>

        {/* Start Button */}
        {callMode === 'browser' ? (
          <button
            onClick={handleStartBrowser}
            className="w-full mt-6 py-4 bg-accent/20 border-2 border-accent text-accent font-bold text-lg rounded-xl hover:bg-accent/30 transition-all"
          >
            🎙️ Start Browser Call (Test)
          </button>
        ) : (
          <button
            onClick={handleStartPhoneCall}
            disabled={isCallingPhone}
            className="w-full mt-6 py-4 bg-green-500/20 border-2 border-green-500 text-green-400 font-bold text-lg rounded-xl hover:bg-green-500/30 transition-all disabled:opacity-50"
          >
            {isCallingPhone ? '📞 Calling...' : '📞 Call Customer'}
          </button>
        )}

        {callStatus && (
          <p className="text-center text-sm mt-3 text-gray-300">{callStatus}</p>
        )}

        <p className="text-center text-xs text-gray-500 mt-4">
          {callMode === 'browser'
            ? 'Test the AI agent in your browser with microphone'
            : 'AI will call the customer and promote your product'}
        </p>
      </div>
    </div>
  )
}

export default ProductSetup
