import { useEffect, useState } from 'react'
import './App.css'
import './buttons.css'

function App() {
  const [equipments, setEquipments] = useState([]);
  const [cmdHistory, setCmdHistory] = useState({});
  const [selectedEqp, setSelectedEqp] = useState('');
  const [cmdName, setCmdName] = useState('START');
  const [newRecipe, setNewRecipe] = useState('RCP-NEW-001');

  const fetchEquipments = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/equipment');
      const data = await res.json();
      setEquipments(data);
      setSelectedEqp(prev => {
        if (!prev && data.length > 0) return data[0].eqp_id;
        return prev;
      });
    } catch (err) {
      console.error(err);
    }
  };

  const fetchCommands = async (eqpId) => {
    try {
      const res = await fetch(`http://localhost:8000/api/equipment/${eqpId}/commands?limit=10`);
      const data = await res.json();
      setCmdHistory(prev => ({...prev, [eqpId]: data}));
    } catch (err) {
      console.error(err);
    }
  };

  const [simEnabled, setSimEnabled] = useState(true);

  const fetchSimulatorState = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/simulator/control');
      const data = await res.json();
      setSimEnabled(data.enabled);
    } catch (err) {
      console.error(err);
    }
  };

  const toggleGlobalSimulator = async () => {
    await fetch(`http://localhost:8000/api/simulator/control?enabled=${!simEnabled}`, { method: 'POST' });
    setSimEnabled(!simEnabled);
  };

  const toggleEqpEnabled = async (eqp) => {
    const action = eqp.enabled ? 'stop' : 'start';
    await fetch(`http://localhost:8000/api/equipment/${eqp.eqp_id}/${action}`, { method: 'POST' });
    fetchEquipments();
  };

  useEffect(() => {
    fetchEquipments();
    fetchSimulatorState();

    const ws = new WebSocket('ws://localhost:8000/api/ws');
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'STATUS_UPDATE' || msg.type === 'COMMAND_REPLY') {
        fetchEquipments();
        if (msg.eqp_id) fetchCommands(msg.eqp_id);
      } else if (msg.type === 'COMMAND_UPDATE') {
        if (msg.eqp_id) fetchCommands(msg.eqp_id);
      }
    };
    return () => ws.close();
  }, []);

  useEffect(() => {
    if (selectedEqp) {
      fetchCommands(selectedEqp);
    }
  }, [selectedEqp]);

  const sendCommand = async () => {
    const params = cmdName === 'CHANGE_RECIPE' ? { recipe_id: newRecipe } : {};
    await fetch(`http://localhost:8000/api/equipment/${selectedEqp}/remote-command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command_name: cmdName, parameters: params })
    });
  };

  return (
    <div className="dashboard">
      <header className="header">
        <div>
          <h1>CIM Equipment Dashboard</h1>
          <button 
            className={`power-btn ${simEnabled ? 'power-on' : 'power-off'}`}
            onClick={toggleGlobalSimulator}
          >
            Global Simulator: {simEnabled ? 'ON' : 'OFF'}
          </button>
        </div>
        <div className="badge">Live WebSocket Connection</div>
      </header>
      
      <main className="main-content">
        <section className="glass-panel">
          <h2>Equipment Overview</h2>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>EQP ID</th>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Simulator Power</th>
                  <th>Recipe</th>
                  <th>Lot ID</th>
                </tr>
              </thead>
              <tbody>
                {equipments.map(eqp => (
                  <tr key={eqp.eqp_id} className={`status-${eqp.current_status.toLowerCase()}`}>
                    <td>{eqp.eqp_id}</td>
                    <td>{eqp.eqp_name}</td>
                    <td>{eqp.eqp_type}</td>
                    <td><span className="status-badge">{eqp.current_status}</span></td>
                    <td>
                      <button 
                        className={`mini-power-btn ${eqp.enabled ? 'mini-on' : 'mini-off'}`}
                        onClick={() => toggleEqpEnabled(eqp)}
                      >
                        {eqp.enabled ? '🟢 Running' : '🔴 Paused'}
                      </button>
                    </td>
                    <td>{eqp.current_recipe_id || '-'}</td>
                    <td>{eqp.current_lot_id || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <div className="bottom-grid">
          <section className="glass-panel">
            <h2>Remote Command Control</h2>
            <div className="control-form">
              <div className="form-group">
                <label>Target Equipment</label>
                <select value={selectedEqp} onChange={e => setSelectedEqp(e.target.value)}>
                  {equipments.map(eqp => <option key={eqp.eqp_id} value={eqp.eqp_id}>{eqp.eqp_id}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Command</label>
                <select value={cmdName} onChange={e => setCmdName(e.target.value)}>
                  <option value="START">START</option>
                  <option value="STOP">STOP</option>
                  <option value="CHANGE_RECIPE">CHANGE_RECIPE</option>
                </select>
              </div>
              {cmdName === 'CHANGE_RECIPE' && (
                <div className="form-group">
                  <label>New Recipe ID</label>
                  <input type="text" value={newRecipe} onChange={e => setNewRecipe(e.target.value)} />
                </div>
              )}
              <button className="primary-btn" onClick={sendCommand}>🚀 Send Command</button>
            </div>
          </section>

          <section className="glass-panel">
            <h2>Recent Commands ({selectedEqp})</h2>
            <div className="table-container small">
              <table>
                <thead>
                  <tr>
                    <th>Command</th>
                    <th>Status</th>
                    <th>Params</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {(cmdHistory[selectedEqp] || []).map(cmd => (
                    <tr key={cmd.id}>
                      <td>{cmd.command_name}</td>
                      <td><span className={`cmd-badge cmd-${cmd.status.toLowerCase()}`}>{cmd.status}</span></td>
                      <td>{JSON.stringify(cmd.parameters)}</td>
                      <td>{new Date(cmd.created_at + 'Z').toLocaleTimeString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}

export default App
