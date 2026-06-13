import { useEffect, useState } from 'react'
import './App.css'
import './buttons.css'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function App() {
  const [page, setPage] = useState('Overview');
  const [equipments, setEquipments] = useState([]);
  const [cmdHistory, setCmdHistory] = useState({});
  const [alarms, setAlarms] = useState([]);
  const [rules, setRules] = useState([]);
  const [sensors, setSensors] = useState([]);
  const [selectedSensorName, setSelectedSensorName] = useState('Temperature');
  const [selectedEqp, setSelectedEqp] = useState('');
  const [alarmPage, setAlarmPage] = useState(1);
  const [rulePage, setRulePage] = useState(1);
  const [cmdName, setCmdName] = useState('START');
  const [newRecipe, setNewRecipe] = useState('RCP-NEW-001');

  // Rule creation states
  const [ruleSensor, setRuleSensor] = useState('Temperature');
  const [ruleCondition, setRuleCondition] = useState('>');
  const [ruleValue, setRuleValue] = useState('85');
  const [ruleCode, setRuleCode] = useState('ALM-001');
  const [ruleMsg, setRuleMsg] = useState('Temperature too high');
  const [ruleEqp, setRuleEqp] = useState('ALL');

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
      const res = await fetch(`http://localhost:8000/api/equipment/${eqpId}/commands`);
      const data = await res.json();
      setCmdHistory(prev => ({ ...prev, [eqpId]: data }));
    } catch (err) {
      console.error(err);
    }
  };

  const fetchAlarms = async (eqpId) => {
    try {
      const res = await fetch(`http://localhost:8000/api/equipment/${eqpId}/alarms`);
      const data = await res.json();
      setAlarms(data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchSensors = async (eqpId) => {
    try {
      const res = await fetch(`http://localhost:8000/api/equipment/${eqpId}/sensors`);
      const data = await res.json();
      setSensors(data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchRules = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/rules');
      const data = await res.json();
      setRules(data);
    } catch (err) {
      console.error(err);
    }
  };

  const createRule = async () => {
    const payload = {
      sensor_name: ruleSensor,
      condition: ruleCondition,
      threshold_value: parseFloat(ruleValue),
      alarm_code: ruleCode,
      alarm_level: 'HIGH',
      alarm_message: ruleMsg
    };
    if (ruleEqp !== 'ALL') {
      payload.eqp_id = ruleEqp;
    }
    await fetch('http://localhost:8000/api/rules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    fetchRules();
  };

  const deleteRule = async (ruleId) => {
    await fetch(`http://localhost:8000/api/rules/${ruleId}`, { method: 'DELETE' });
    fetchRules();
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
    fetchRules();

    const ws = new WebSocket('ws://localhost:8000/api/ws');
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'STATUS_UPDATE' || msg.type === 'COMMAND_REPLY' || msg.type === 'ALARM_UPDATE') {
        fetchEquipments();
        if (msg.eqp_id) {
          fetchCommands(msg.eqp_id);
          fetchAlarms(msg.eqp_id);
          fetchSensors(msg.eqp_id);
        }
      } else if (msg.type === 'COMMAND_UPDATE') {
        if (msg.eqp_id) fetchCommands(msg.eqp_id);
      }
    };
    return () => ws.close();
  }, []);

  useEffect(() => {
    if (selectedEqp) {
      setAlarmPage(1);
      fetchCommands(selectedEqp);
      fetchAlarms(selectedEqp);
      fetchSensors(selectedEqp);
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

  const renderContent = () => {
    if (page === 'Overview') {
      return (
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
      );
    }

    if (page === 'Control') {
      return (
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
      );
    }

    if (page === 'Sensors') {
      const filteredSensors = sensors.filter(s => s.sensor_name === selectedSensorName);
      // Format data for Recharts
      const chartData = filteredSensors.map(s => ({
        time: new Date(s.collected_at + 'Z').toLocaleTimeString(),
        value: s.sensor_value
      })).reverse(); // Reverse to get chronological order if it was DESC

      return (
        <section className="glass-panel">
          <h2>Sensor Trends</h2>
          <div className="control-form" style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
            <div className="form-group">
              <label>Target Equipment</label>
              <select value={selectedEqp} onChange={e => setSelectedEqp(e.target.value)}>
                {equipments.map(eqp => <option key={eqp.eqp_id} value={eqp.eqp_id}>{eqp.eqp_id}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Sensor</label>
              <select value={selectedSensorName} onChange={e => setSelectedSensorName(e.target.value)}>
                <option value="Temperature">Temperature</option>
                <option value="Pressure">Pressure</option>
              </select>
            </div>
          </div>
          
          <div style={{ height: 400, marginTop: '2rem' }}>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis dataKey="time" stroke="#9ca3af" />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip contentStyle={{ backgroundColor: 'rgba(17, 24, 39, 0.9)', border: 'none', borderRadius: '8px', color: '#fff' }} />
                  <Legend />
                  <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 8 }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p>No sensor data available.</p>
            )}
          </div>
        </section>
      );
    }

    if (page === 'Alarms') {
      const alarmsPerPage = 10;
      const totalPages = Math.ceil(alarms.length / alarmsPerPage) || 1;
      const currentAlarms = alarms.slice((alarmPage - 1) * alarmsPerPage, alarmPage * alarmsPerPage);

      const rulesPerPage = 10;
      const totalRulePages = Math.ceil(rules.length / rulesPerPage) || 1;
      const currentRules = rules.slice((rulePage - 1) * rulesPerPage, rulePage * rulesPerPage);

      return (
        <div className="grid-2-col">
          <section className="glass-panel">
            <h2>Alarm Logs</h2>
            <div className="control-form" style={{ marginBottom: '1rem' }}>
              <div className="form-group">
                <label>Target Equipment</label>
                <select value={selectedEqp} onChange={e => setSelectedEqp(e.target.value)}>
                  {equipments.map(eqp => <option key={eqp.eqp_id} value={eqp.eqp_id}>{eqp.eqp_id}</option>)}
                </select>
              </div>
            </div>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Code</th>
                    <th>Level</th>
                    <th>Message</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {currentAlarms.map((al, idx) => (
                    <tr key={idx} className={`alarm-${al.alarm_level?.toLowerCase()}`}>
                      <td>{new Date(al.occurred_at + 'Z').toLocaleString()}</td>
                      <td>{al.alarm_code}</td>
                      <td>{al.alarm_level}</td>
                      <td>{al.alarm_message}</td>
                      <td>{al.alarm_status}</td>
                    </tr>
                  ))}
                  {alarms.length === 0 && <tr><td colSpan="5">No recent alarms</td></tr>}
                </tbody>
              </table>
            </div>
            {alarms.length > 0 && (
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
                <button 
                  className="primary-btn" 
                  style={{ background: 'transparent', border: '1px solid var(--glass-border)', color: '#fff', visibility: alarmPage === 1 ? 'hidden' : 'visible' }}
                  onClick={() => setAlarmPage(p => Math.max(1, p - 1))}
                  disabled={alarmPage === 1}
                >
                  Prev
                </button>
                <span style={{ color: '#9ca3af' }}>Page {alarmPage} of {totalPages}</span>
                <button 
                  className="primary-btn" 
                  style={{ background: 'transparent', border: '1px solid var(--glass-border)', color: '#fff', visibility: alarmPage === totalPages ? 'hidden' : 'visible' }}
                  onClick={() => setAlarmPage(p => Math.min(totalPages, p + 1))}
                  disabled={alarmPage === totalPages}
                >
                  Next
                </button>
              </div>
            )}
          </section>

          <section className="glass-panel">
            <h2>Alarm Rules Engine</h2>
            <div className="table-container" style={{ marginTop: '1rem', overflow: 'visible' }}>
              <table>
                <thead>
                  <tr>
                    <th>Equipment</th>
                    <th>Sensor</th>
                    <th>Condition</th>
                    <th>Value</th>
                    <th>Code</th>
                    <th>Message</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="add-rule-row">
                    <td>
                      <select className="inline-input" value={ruleEqp} onChange={e => setRuleEqp(e.target.value)}>
                        <option value="ALL">All</option>
                        {equipments.map(eqp => <option key={eqp.eqp_id} value={eqp.eqp_id}>{eqp.eqp_id}</option>)}
                      </select>
                    </td>
                    <td>
                      <select className="inline-input" value={ruleSensor} onChange={e => setRuleSensor(e.target.value)}>
                        <option value="Temperature">Temperature</option>
                        <option value="Pressure">Pressure</option>
                      </select>
                    </td>
                    <td>
                      <select className="inline-input" value={ruleCondition} onChange={e => setRuleCondition(e.target.value)}>
                        <option value=">">&gt;</option>
                        <option value="<">&lt;</option>
                        <option value="==">==</option>
                      </select>
                    </td>
                    <td><input className="inline-input" type="number" value={ruleValue} onChange={e => setRuleValue(e.target.value)} placeholder="Value" /></td>
                    <td><input className="inline-input" type="text" value={ruleCode} onChange={e => setRuleCode(e.target.value)} placeholder="Code" /></td>
                    <td><input className="inline-input" type="text" value={ruleMsg} onChange={e => setRuleMsg(e.target.value)} placeholder="Message" /></td>
                    <td><button className="primary-btn" style={{ margin: 0 }} onClick={createRule}>Add</button></td>
                  </tr>
                  {currentRules.map(r => (
                    <tr key={r.id}>
                      <td>{r.eqp_id || 'ALL'}</td>
                      <td>{r.sensor_name}</td>
                      <td>{r.condition}</td>
                      <td>{r.threshold_value}</td>
                      <td>{r.alarm_code}</td>
                      <td>{r.alarm_message}</td>
                      <td><button onClick={() => deleteRule(r.id)}>Delete</button></td>
                    </tr>
                  ))}
                  {rules.length === 0 && <tr><td colSpan="7">No rules</td></tr>}
                </tbody>
              </table>
            </div>
            {rules.length > 0 && (
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
                <button 
                  className="primary-btn" 
                  style={{ background: 'transparent', border: '1px solid var(--glass-border)', color: '#fff', visibility: rulePage === 1 ? 'hidden' : 'visible' }}
                  onClick={() => setRulePage(p => Math.max(1, p - 1))}
                  disabled={rulePage === 1}
                >
                  Prev
                </button>
                <span style={{ color: '#9ca3af' }}>Page {rulePage} of {totalRulePages}</span>
                <button 
                  className="primary-btn" 
                  style={{ background: 'transparent', border: '1px solid var(--glass-border)', color: '#fff', visibility: rulePage === totalRulePages ? 'hidden' : 'visible' }}
                  onClick={() => setRulePage(p => Math.min(totalRulePages, p + 1))}
                  disabled={rulePage === totalRulePages}
                >
                  Next
                </button>
              </div>
            )}
          </section>
        </div>
      );
    }
  };

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <h2>Control Panel</h2>
        <ul className="sidebar-nav">
          <li className={page === 'Overview' ? 'active' : ''} onClick={() => setPage('Overview')}>Overview</li>
          <li className={page === 'Control' ? 'active' : ''} onClick={() => setPage('Control')}>Remote Control</li>
          <li className={page === 'Sensors' ? 'active' : ''} onClick={() => setPage('Sensors')}>Sensor Trends</li>
          <li className={page === 'Alarms' ? 'active' : ''} onClick={() => setPage('Alarms')}>Alarms & Rules</li>
        </ul>
        <div style={{ marginTop: 'auto', paddingTop: '2rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
          <h3 style={{ fontSize: '1rem', color: '#9ca3af', marginBottom: '1rem' }}>Simulator System</h3>
          <button 
            className={`power-btn ${simEnabled ? 'power-on' : 'power-off'}`}
            onClick={toggleGlobalSimulator}
            style={{ width: '100%', justifyContent: 'center' }}
          >
            Power: {simEnabled ? 'ON' : 'OFF'}
          </button>
        </div>
      </aside>

      <div className="main-wrapper">
        <header className="header" style={{ borderRadius: 0, margin: 0 }}>
          <div>
            <h1>CIM Equipment Dashboard</h1>
          </div>
          <div className="badge">Live WebSocket Connection</div>
        </header>
        
        <main className="main-content">
          {renderContent()}
        </main>
      </div>
    </div>
  )
}

export default App

