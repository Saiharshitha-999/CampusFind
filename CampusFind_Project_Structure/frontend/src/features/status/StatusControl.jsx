import { useState } from 'react'
import { request } from '../../api/client.js'

const nextStatuses={'Approved for Return':['Returned']}

export function StatusControl({item,onChange,onError}) {
  const [busy,setBusy]=useState(false)
  const options=nextStatuses[item.status]||[]
  if(!options.length)return <>—</>
  async function update(event) {
    const status=event.target.value
    if(!status)return
    setBusy(true)
    try { await request(`/items/${item.id}/status`,{method:'POST',body:JSON.stringify({status})}); await onChange() }
    catch(error) { onError(error.message) }
    finally { setBusy(false); event.target.value='' }
  }
  return <select aria-label={`Update ${item.item_name} status`} disabled={busy} defaultValue="" onChange={update}><option value="">{busy?'Updating…':'Change status…'}</option>{options.map(status=><option key={status} value={status}>{status}</option>)}</select>
}
