import { useState, useEffect } from 'react';
import EntityForm from './components/EntityForm';
import ReportModeSelector from './components/ReportModeSelector';
import TransactionForm from './components/TransactionForm';
import ReportDisplay from './components/ReportDisplay';
import { getSections, calculateTDS, downloadExcel } from './services/api';
import './App.css';

const getDefaultTransaction = () => ({
  section_code: '',
  amount: 0,
  category: 'Company / Firm / Co-operative Society / Local Authority',
  pan_available: true,
  deduction_date: new Date().toISOString().split('T')[0],
  payment_date: new Date().toISOString().split('T')[0],
  threshold_type: '',
  annual_threshold_exceeded: false,
  selected_slab: '',
});

function App() {
  const [step, setStep] = useState(1);
  const [entity, setEntity] = useState(null);
  const [mode, setMode] = useState('single');
  const [transactions, setTransactions] = useState([getDefaultTransaction()]);
  const [currentTransactionIndex, setCurrentTransactionIndex] = useState(0);
  const [totalTransactions, setTotalTransactions] = useState(1);
  const [sections, setSections] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSections = async () => {
      try {
        const data = await getSections();
        setSections(data);
      } catch (err) {
        setError('Failed to load TDS sections. Make sure the backend server is running.');
        console.error(err);
      }
    };
    fetchSections();
  }, []);

  const handleEntitySubmit = (entityData) => {
    setEntity(entityData);
    setStep(2);
  };

  const handleModeSelect = () => {
    if (mode === 'multiple') {
      setStep(2.5); // Go to transaction count selection
    } else {
      setTransactions([getDefaultTransaction()]);
      setCurrentTransactionIndex(0);
      setTotalTransactions(1);
      setStep(3);
    }
  };

  const handleSetTransactionCount = (count) => {
    const newTransactions = Array(count).fill(null).map(() => getDefaultTransaction());
    setTransactions(newTransactions);
    setTotalTransactions(count);
    setCurrentTransactionIndex(0);
    setStep(3);
  };

  const handleTransactionChange = (newTransaction) => {
    const updated = [...transactions];
    updated[currentTransactionIndex] = newTransaction;
    setTransactions(updated);
  };

  const handleNextTransaction = () => {
    if (currentTransactionIndex < totalTransactions - 1) {
      setCurrentTransactionIndex(currentTransactionIndex + 1);
    }
  };

  const handlePrevTransaction = () => {
    if (currentTransactionIndex > 0) {
      setCurrentTransactionIndex(currentTransactionIndex - 1);
    }
  };

  const validateCurrentTransaction = () => {
    const txn = transactions[currentTransactionIndex];
    if (!txn.section_code) {
      setError(`Please select a TDS section`);
      return false;
    }
    if (txn.amount <= 0) {
      setError(`Please enter a valid amount`);
      return false;
    }
    if (!txn.deduction_date || !txn.payment_date) {
      setError(`Please enter valid dates`);
      return false;
    }
    return true;
  };

  const validateAllTransactions = () => {
    for (let i = 0; i < transactions.length; i++) {
      const txn = transactions[i];
      if (!txn.section_code) {
        setError(`Transaction ${i + 1}: Please select a TDS section`);
        return false;
      }
      if (txn.amount <= 0) {
        setError(`Transaction ${i + 1}: Please enter a valid amount`);
        return false;
      }
      if (!txn.deduction_date || !txn.payment_date) {
        setError(`Transaction ${i + 1}: Please enter valid dates`);
        return false;
      }
    }
    return true;
  };

  const handleCalculate = async () => {
    setError(null);
    if (!validateAllTransactions()) return;

    setLoading(true);
    try {
      const response = await calculateTDS(entity, transactions);
      setResults(response.results);
      setStep(4);
    } catch (err) {
      setError('Failed to calculate TDS. Please check your inputs and try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadExcel = async () => {
    setLoading(true);
    try {
      await downloadExcel(entity, results);
    } catch (err) {
      setError('Failed to download Excel. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setResults(null);
    setTransactions([getDefaultTransaction()]);
    setCurrentTransactionIndex(0);
    setTotalTransactions(1);
    setStep(1);
    setEntity(null);
    setMode('single');
  };

  const handleBackToMode = () => {
    setStep(2);
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>
            <span className="header-icon">🧮</span>
            TDS Calculator
          </h1>
          <p>Financial Year 2025-2026 | Non-Salary Payments</p>
        </div>
      </header>

      <main className="app-main">
        {error && (
          <div className="error-banner">
            <span>⚠️</span>
            <span>{error}</span>
            <button onClick={() => setError(null)}>✕</button>
          </div>
        )}

        {/* Step 1: Entity Form */}
        {step === 1 && (
          <EntityForm onSubmit={handleEntitySubmit} initialData={entity} />
        )}

        {/* Step 2: Report Mode Selection */}
        {step === 2 && (
          <div className="step-container">
            <ReportModeSelector mode={mode} onModeChange={setMode} />
            <div className="step-actions">
              <button className="back-btn" onClick={() => setStep(1)}>
                ← Back
              </button>
              <button className="continue-btn" onClick={handleModeSelect}>
                Continue →
              </button>
            </div>
          </div>
        )}

        {/* Step 2.5: Transaction Count Selection (Multiple Mode Only) */}
        {step === 2.5 && (
          <div className="transaction-count-container">
            <div className="count-header">
              <div className="count-icon">📚</div>
              <h2>How many transactions?</h2>
              <p>Enter the number of transactions you want to calculate</p>
            </div>

            <div className="count-input-wrapper">
              <button
                className="count-btn"
                onClick={() => totalTransactions > 1 && setTotalTransactions(totalTransactions - 1)}
                disabled={totalTransactions <= 1}
              >
                −
              </button>
              <input
                type="number"
                className="count-input"
                value={totalTransactions}
                onChange={(e) => setTotalTransactions(Math.max(1, Math.min(20, parseInt(e.target.value) || 1)))}
                min="1"
                max="20"
              />
              <button
                className="count-btn"
                onClick={() => totalTransactions < 20 && setTotalTransactions(totalTransactions + 1)}
                disabled={totalTransactions >= 20}
              >
                +
              </button>
            </div>
            <p className="count-hint">Maximum 20 transactions</p>

            <div className="step-actions">
              <button className="back-btn" onClick={() => setStep(2)}>
                ← Back
              </button>
              <button className="continue-btn" onClick={() => handleSetTransactionCount(totalTransactions)}>
                Continue to Transactions →
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Transaction Entry */}
        {step === 3 && (
          <div className="transactions-container">
            {/* Progress Indicator for Multiple Mode */}
            {mode === 'multiple' && (
              <div className="transaction-progress">
                <div className="progress-header">
                  <span className="progress-title">📋 Transaction Progress</span>
                  <span className="progress-count">
                    {currentTransactionIndex + 1} of {totalTransactions}
                  </span>
                </div>
                <div className="progress-bar-container">
                  <div
                    className="progress-bar"
                    style={{ width: `${((currentTransactionIndex + 1) / totalTransactions) * 100}%` }}
                  />
                </div>
                <div className="progress-steps">
                  {Array(totalTransactions).fill(null).map((_, idx) => (
                    <button
                      key={idx}
                      className={`progress-step ${idx === currentTransactionIndex ? 'active' : ''} ${idx < currentTransactionIndex ? 'completed' : ''} ${transactions[idx]?.section_code ? 'filled' : ''}`}
                      onClick={() => setCurrentTransactionIndex(idx)}
                      title={`Transaction ${idx + 1}`}
                    >
                      {idx < currentTransactionIndex ? '✓' : idx + 1}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="transactions-header">
              <h2>
                <span>💼</span>
                {mode === 'single' ? 'Transaction Details' : `Transaction ${currentTransactionIndex + 1} of ${totalTransactions}`}
              </h2>
            </div>

            <div className="entity-summary">
              <span>🏢 {entity.entity_name}</span>
              <span>🆔 {entity.pan_number}</span>
            </div>

            <TransactionForm
              key={currentTransactionIndex}
              sections={sections}
              transaction={transactions[currentTransactionIndex]}
              onChange={handleTransactionChange}
              onRemove={() => { }}
              showRemove={false}
              index={currentTransactionIndex}
            />

            <div className="form-actions">
              {mode === 'single' ? (
                <>
                  <button className="back-btn" onClick={handleBackToMode}>
                    ← Back
                  </button>
                  <button
                    className="calculate-btn"
                    onClick={handleCalculate}
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <span className="spinner"></span>
                        Calculating...
                      </>
                    ) : (
                      <>
                        🔢 Calculate TDS
                      </>
                    )}
                  </button>
                </>
              ) : (
                <>
                  <button
                    className="back-btn"
                    onClick={currentTransactionIndex === 0 ? () => setStep(2.5) : handlePrevTransaction}
                  >
                    ← {currentTransactionIndex === 0 ? 'Back' : 'Previous'}
                  </button>

                  {currentTransactionIndex < totalTransactions - 1 ? (
                    <button
                      className="next-btn"
                      onClick={() => {
                        setError(null);
                        if (validateCurrentTransaction()) {
                          handleNextTransaction();
                        }
                      }}
                    >
                      Next Transaction →
                    </button>
                  ) : (
                    <button
                      className="calculate-btn"
                      onClick={handleCalculate}
                      disabled={loading}
                    >
                      {loading ? (
                        <>
                          <span className="spinner"></span>
                          Calculating All...
                        </>
                      ) : (
                        <>
                          🔢 Calculate All {totalTransactions} Reports
                        </>
                      )}
                    </button>
                  )}
                </>
              )}
            </div>

            {/* Transaction Summary in Multiple Mode */}
            {mode === 'multiple' && (
              <div className="transactions-summary">
                <h4>📊 Transactions Summary</h4>
                <div className="summary-list">
                  {transactions.map((txn, idx) => (
                    <div
                      key={idx}
                      className={`summary-item ${idx === currentTransactionIndex ? 'active' : ''} ${txn.section_code ? 'filled' : 'empty'}`}
                      onClick={() => setCurrentTransactionIndex(idx)}
                    >
                      <span className="summary-num">{idx + 1}</span>
                      <span className="summary-section">
                        {txn.section_code ? `Section ${txn.section_code}` : 'Not filled'}
                      </span>
                      <span className="summary-amount">
                        {txn.amount > 0 ? `₹${txn.amount.toLocaleString('en-IN')}` : '—'}
                      </span>
                      <span className="summary-status">
                        {txn.section_code && txn.amount > 0 ? '✓' : '○'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step 4: Results Display */}
        {step === 4 && results && (
          <ReportDisplay
            entity={entity}
            results={results}
            onDownloadExcel={handleDownloadExcel}
            onBack={handleBack}
            loading={loading}
          />
        )}
      </main>

      <footer className="app-footer">
        <p>📌 Disclaimer: This calculator is for informational purposes only.</p>
      </footer>
    </div>
  );
}

export default App;
