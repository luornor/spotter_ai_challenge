// Minimal canvas renderer that draws activity blocks on a 24-hour grid
import { useEffect, useRef } from 'react'

const ROWS = [ 'off_duty', 'sleeper', 'driving', 'on_duty' ] as const

type Block = { status: 'off_duty'|'sleeper'|'driving'|'on_duty', start: string, end: string }

function toMinutes(t: string){
  const [h,m] = t.split(':').map(Number)
  return h*60 + m
}

export default function LogCanvas({ blocks }: { blocks: Block[] }){
  const ref = useRef<HTMLCanvasElement | null>(null)
  const left = 110          // where 00:00 starts
  const rightPad = 30       // right edge margin
  const yMid0 = 256         // ANCHOR: centerline of row 1 (Off Duty)
  let rowH = 32             // spacing between rows (reduce to tighten)
  const hourLabelY = 214    // y-position for red hour labels
  const lineWidth = 3


  useEffect(() => {
    const canvas = ref.current!
    const ctx = canvas.getContext('2d')!
    const W = canvas.width
    const H = canvas.height

    const img = new Image()
    img.src = '/log.png' // place this image in frontend/public/
    img.onload = () => {
      ctx.clearRect(0, 0, W, H)
      ctx.drawImage(img, 0, 0, W, H)
    
    // These coordinates align the overlay with the time graph region of your image.
      // Tweak if needed to match perfectly:
    const right = W - rightPad
    const top = yMid0 - rowH / 2 

    // hour labels (in red)
    ctx.fillStyle = '#d33'
    ctx.font = '14px sans-serif'
    for (let h = 0; h <= 24; h++) {
      const x = left + (h / 24) * (right - left)
      if (h % 2 === 0) {
        ctx.fillText(String(h).padStart(2, '0'), x - 8, hourLabelY)
      }
    }
    
    // activity lines
    ctx.strokeStyle = '#23c552' // your green
    ctx.lineWidth = lineWidth
    blocks.forEach((b) => {
      const rowIndex = ROWS.indexOf(b.status)
      const y = top + rowIndex * rowH + rowH / 2
      const x1 = left + (toMinutes(b.start) / 1440) * (right - left)
      const x2 = left + (toMinutes(b.end) / 1440) * (right - left)
      ctx.beginPath()
      ctx.moveTo(x1, y)
      ctx.lineTo(x2, y)
      ctx.stroke()
    })
    };
  }, [blocks, left, rightPad, yMid0, rowH, hourLabelY, lineWidth])

  return <canvas ref={ref} width={900} height={650} style={{ width: '100%', border: '1px solid #eee', borderRadius: 8, background: '#fff' }} />
}

