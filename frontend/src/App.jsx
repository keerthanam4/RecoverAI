import { useEffect, useMemo, useState } from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

function formatINR(value) {
  return `₹${Number(value).toLocaleString("en-IN", {
    maximumFractionDigits: 2,
  })}`;
}

function formatLakhs(value) {
  return `₹${(Number(value) / 100000).toFixed(2)}L`;
}

function App() {
  const [summary, setSummary] = useState(null);
  const [actions, setActions] = useState([]);
  const [opportunities, setOpportunities] = useState([]);
  const [evaluation, setEvaluation] = useState(null);
  const [executions, setExecutions] = useState([]);
  const [selectedTransaction, setSelectedTransaction] =
    useState(null);
  const [opportunitySearch, setOpportunitySearch] = useState("");
  const [opportunityAction, setOpportunityAction] = useState("ALL");
  const [opportunityStatus, setOpportunityStatus] = useState("ALL");
  const [opportunityHumanReview, setOpportunityHumanReview] = useState("ALL");

  const [recoveryLoading, setRecoveryLoading] =
    useState(false);
  const [executionLoading, setExecutionLoading] =
    useState(false);

  const [recoveryError, setRecoveryError] =
    useState("");

  const [existingExecution, setExistingExecution] =
    useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        setLoading(true);

        const [
          summaryResponse,
          actionsResponse,
          opportunitiesResponse,
          executionsResponse,
          evaluationResponse,
        ] = await Promise.all([
          fetch(`${API_BASE}/api/summary`),
          fetch(`${API_BASE}/api/actions`),
          fetch(`${API_BASE}/api/opportunities?limit=50`),
          fetch(`${API_BASE}/api/executions`),
          fetch(`${API_BASE}/api/evaluation`),
        ]);

        if (
          !summaryResponse.ok ||
          !actionsResponse.ok ||
          !opportunitiesResponse.ok ||
          !executionsResponse.ok ||
          !evaluationResponse.ok
        ) {
          throw new Error(
            "Backend API request failed."
          );
        }

        const summaryData =
          await summaryResponse.json();

        const actionsData =
          await actionsResponse.json();

        const opportunitiesData =
          await opportunitiesResponse.json();

        const executionsData =
          await executionsResponse.json();

        const evaluationData =
          await evaluationResponse.json();

        setSummary(summaryData);

        setActions(
          actionsData.actions || []
        );

        setOpportunities(
          opportunitiesData.opportunities || []
        );

        setExecutions(
          executionsData.executions || []
        );

        setEvaluation(
          evaluationData
        );

        setError("");
      } catch (err) {
        console.error(err);

        setError(
          "Unable to connect to the RecoverAI backend."
        );
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);
  const filteredOpportunities = useMemo(() => {
    return opportunities.filter((item) => {
      const matchesSearch =
        !opportunitySearch ||
        String(item.transaction_id)
          .toLowerCase()
          .includes(opportunitySearch.toLowerCase());

      const matchesAction =
        opportunityAction === "ALL" ||
        item.recommended_action === opportunityAction;

      const matchesStatus =
        opportunityStatus === "ALL" ||
        String(item.payment_status).toUpperCase() ===
        opportunityStatus;

      const matchesHumanReview =
        opportunityHumanReview === "ALL" ||
        (opportunityHumanReview === "REQUIRED" &&
          item.requires_human === true) ||
        (opportunityHumanReview === "NOT_REQUIRED" &&
          item.requires_human === false);

      return (
        matchesSearch &&
        matchesAction &&
        matchesStatus &&
        matchesHumanReview
      );
    });
  }, [
    opportunities,
    opportunitySearch,
    opportunityAction,
    opportunityStatus,
    opportunityHumanReview,
  ]);

  async function openRecoveryConsole(transactionId) {
    try {
      setRecoveryLoading(true);
      setRecoveryError("");
      setExistingExecution(null);

      const response = await fetch(
        `${API_BASE}/api/recovery/${transactionId}`
      );

      if (!response.ok) {
        throw new Error(
          "Unable to load recovery details."
        );
      }

      const data = await response.json();

      if (!data.found) {
        throw new Error(
          "Transaction was not found."
        );
      }

      setSelectedTransaction(
        data.transaction
      );

      setTimeout(() => {
        document
          .getElementById("recovery-console")
          ?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
      }, 100);

      const executionResponse = await fetch(
        `${API_BASE}/api/executions`
      );

      if (executionResponse.ok) {
        const executionData =
          await executionResponse.json();

        const successfulExecution =
          executionData.executions.find(
            (execution) =>
              execution.transaction_id ===
              transactionId &&
              (
                execution.execution_status === "CREATED" ||
                execution.execution_status === "ALREADY_EXECUTED"
              )
          );

        if (successfulExecution) {
          setExistingExecution(
            successfulExecution
          );
        }
      }
    } catch (err) {
      console.error(err);
      setRecoveryError(err.message);
    } finally {
      setRecoveryLoading(false);
    }
  }
  async function executeRecovery(transactionId) {
    try {
      setExecutionLoading(true);
      setRecoveryError("");

      const response = await fetch(
        `${API_BASE}/api/recovery/${transactionId}/execute`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(
          data.message ||
          data.error ||
          "Recovery execution failed."
        );
      }

      // Refresh the selected transaction so the UI
      // reflects the new execution status.
      const detailResponse = await fetch(
        `${API_BASE}/api/recovery/${transactionId}`
      );

      if (detailResponse.ok) {
        const detailData = await detailResponse.json();

        if (detailData.found) {
          setSelectedTransaction(detailData.transaction);
        }
      }

      // Refresh execution audit data.
      const executionResponse = await fetch(
        `${API_BASE}/api/executions`
      );

      if (executionResponse.ok) {
        const executionData =
          await executionResponse.json();

        setExecutions(
          executionData.executions || []
        );

        const successfulExecution =
          executionData.executions.find(
            (execution) =>
              execution.transaction_id ===
              transactionId &&
              (
                execution.execution_status === "CREATED" ||
                execution.execution_status ===
                "ALREADY_EXECUTED"
              )
          );

        if (successfulExecution) {
          setExistingExecution(
            successfulExecution
          );
        }
      }

      // Refresh dashboard metrics.
      const summaryResponse = await fetch(
        `${API_BASE}/api/summary`
      );

      if (summaryResponse.ok) {
        const summaryData =
          await summaryResponse.json();

        setSummary(summaryData);
      }
    } catch (err) {
      console.error(err);

      setRecoveryError(
        err.message ||
        "Recovery execution failed."
      );
    } finally {
      setRecoveryLoading(false);
    }
  }

  const totalActionDecisions = useMemo(
    () =>
      actions.reduce(
        (total, action) =>
          total + action.value,
        0
      ),
    [actions]
  );

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-card">
          <div className="loading-mark">
            R
          </div>

          <h2>RecoverAI</h2>

          <p>
            Loading recovery intelligence...
          </p>
        </div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="loading-screen">
        <div className="error-card">
          <div className="error-mark">
            !
          </div>

          <h2>
            Backend connection failed
          </h2>

          <p>{error}</p>

          <code>
            http://127.0.0.1:8000
          </code>

          <p>
            Make sure the Uvicorn server is running.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">

      <header className="topbar">
        <div className="brand">

          <div className="brand-mark">
            R
          </div>

          <div>
            <div className="brand-name">
              RecoverAI
            </div>

            <div className="brand-subtitle">
              AI Revenue Recovery Control Center
            </div>
          </div>

        </div>

        <div className="environment">
          <span className="status-dot"></span>
          Razorpay Test Mode
        </div>
      </header>


      <main className="dashboard">

        {/* =====================================================
            HERO
        ===================================================== */}

        <section className="hero">

          <div>

            <p className="eyebrow">
              REVENUE RECOVERY
            </p>

            <h1>
              Recover revenue before
              <br />
              it disappears.
            </h1>

            <p className="hero-text">
              RecoverAI detects at-risk payments,
              predicts recovery probability, selects
              the safest intervention, and executes
              bounded recovery workflows.
            </p>

          </div>

          <div className="hero-badge">

            <span>AI</span>

            <div>
              <strong>
                Agent active
              </strong>

              <small>
                Policy-gated execution
              </small>
            </div>

          </div>

        </section>


        {/* =====================================================
            EXECUTIVE METRICS
        ===================================================== */}

        <section className="metrics-grid">

          <MetricCard
            label="REVENUE AT RISK"
            value={formatLakhs(
              summary.revenue_at_risk
            )}
            description="Capital currently exposed across failed and abandoned payments"
          />

          <MetricCard
            label="EXPECTED RECOVERY"
            value={formatLakhs(
              summary.expected_recovery
            )}
            description="Probability-weighted revenue RecoverAI expects to recover"
          />

          <MetricCard
            label="RECOVERY OPPORTUNITIES"
            value={summary.recovery_opportunities.toLocaleString()}
            description="Transactions identified as actionable recovery candidates"
          />

          <MetricCard
            label="HUMAN ESCALATIONS"
            value={summary.human_escalations.toLocaleString()}
            description="Cases automatically routed for controlled human review"
          />

        </section>

        {/* =====================================================
            RECOVERY IMPACT
        ===================================================== */}

        <section className="panel recovery-impact-panel">

          <div className="section-heading">

            <div>

              <span className="console-label">
                RECOVERY IMPACT
              </span>

              <h2>
                Model validation & historical outcomes
              </h2>

              <p>
                Historical recovery outcomes compared
                with RecoverAI's estimates.
              </p>

            </div>

          </div>


          {evaluation && (
            <>

              <div className="impact-grid">

                <div className="impact-card">

                  <span className="console-label">
                    HISTORICAL RECOVERY
                  </span>

                  <strong>
                    ₹
                    {(
                      evaluation.historical_recovery /
                      100000
                    ).toFixed(2)}
                    L
                  </strong>

                  <small>
                    {
                      evaluation.recovered_transactions
                    }{" "}
                    recovered opportunities
                  </small>

                </div>


                <div className="impact-card">

                  <span className="console-label">
                    OPPORTUNITY RECOVERY RATE
                  </span>

                  <strong>
                    {evaluation.recovery_rate.toFixed(
                      2
                    )}
                    %
                  </strong>

                  <small>
                    {
                      evaluation.recovered_transactions
                    }{" "}
                    of{" "}
                    {
                      evaluation.recovery_opportunities
                    }{" "}
                    opportunities recovered
                  </small>

                </div>


                <div className="impact-card">

                  <span className="console-label">
                    ESTIMATE ALIGNMENT
                  </span>

                  <strong>
                    {evaluation.estimate_alignment.toFixed(
                      2
                    )}
                    %
                  </strong>

                  <small>
                    Expected vs historical recovered revenue
                  </small>

                </div>


                <div className="impact-card">

                  <span className="console-label">
                    PROBABILITY SEPARATION
                  </span>

                  <strong>
                    {evaluation.probability_separation.toFixed(
                      4
                    )}
                  </strong>

                  <small>
                    Recovered vs non-recovered probability
                  </small>

                </div>

              </div>


              <div className="strategy-performance">

                <div className="strategy-header">

                  <div>

                    <span className="console-label">
                      HISTORICAL OUTCOMES
                    </span>

                    <h3>
                      Recovery performance by strategy
                    </h3>

                    <p className="strategy-insight">
                      Payment-link recovery currently shows the
                      strongest historical recovery rate, supporting
                      RecoverAI's strategy-based intervention model.
                    </p>

                  </div>

                  <span className="evidence-badge">
                    OUTCOME VALIDATED
                  </span>

                </div>


                {[
                  "RETRY",
                  "PAYMENT_LINK",
                  "REMINDER",
                  "ESCALATE",
                  "STOP",
                ].map((action) => {

                  const strategy =
                    evaluation.strategy_performance?.[
                    action
                    ];

                  if (!strategy) {
                    return null;
                  }

                  return (
                    <div
                      className="strategy-row"
                      key={action}
                    >

                      <div className="strategy-name">

                        <strong>
                          {action}
                        </strong>

                        <small>
                          {strategy.recovered.toLocaleString()}
                          {" "}
                          /{" "}
                          {strategy.transactions.toLocaleString()}
                          {" "}
                          recovered
                        </small>

                      </div>


                      <div className="strategy-bar">

                        <div
                          className="strategy-bar-fill"
                          style={{
                            width: `${strategy.recovery_rate}%`,
                          }}
                        />

                      </div>


                      <strong className="strategy-rate">
                        {strategy.recovery_rate.toFixed(
                          2
                        )}
                        %
                      </strong>

                    </div>
                  );
                })}

              </div>

            </>
          )}

        </section>


        {/* =====================================================
            DECISION ENGINE + EXECUTION
        ===================================================== */}

        <section className="content-grid">

          <div className="panel strategy-panel">

            <div className="panel-header">

              <div>

                <p className="section-label">
                  DECISION ENGINE
                </p>

                <h2>
                  AI recovery decision engine
                </h2>

                <p className="panel-description">
                  RecoverAI evaluates transaction risk, recovery probability,
                  expected value, and policy constraints before selecting
                  the safest recovery strategy.
                </p>

              </div>

              <span className="panel-count">
                {totalActionDecisions.toLocaleString()}{" "}
                decisions
              </span>

            </div>


            <div className="action-list">

              {actions.map((item) => {

                const percentage =
                  totalActionDecisions
                    ? (item.value /
                      totalActionDecisions) *
                    100
                    : 0;

                const cssName = item.name
                  .toLowerCase()
                  .replaceAll(" ", "-");

                return (
                  <div
                    className="action-row"
                    key={item.name}
                  >

                    <div className="action-info">

                      <span
                        className={`action-indicator ${cssName}`}
                      ></span>

                      <span className="action-name">
                        {item.name}
                      </span>

                    </div>


                    <div className="action-bar">

                      <div
                        className="action-fill"
                        style={{
                          width: `${percentage}%`,
                        }}
                      ></div>

                    </div>


                    <div className="action-value">
                      {item.value.toLocaleString()}
                    </div>

                  </div>
                );
              })}

            </div>


            <div className="automation-box">

              <div>

                <span>
                  Automation rate
                </span>

                <strong>
                  {summary.automation_rate}%
                </strong>

              </div>


              <div className="progress-track">

                <div
                  className="progress-fill"
                  style={{
                    width: `${summary.automation_rate}%`,
                  }}
                ></div>

              </div>


              <small>
                {summary.automated_actions.toLocaleString()}{" "}
                decisions are eligible for bounded automation;
                higher-risk cases remain under human control.
              </small>

            </div>

          </div>


          <div className="panel execution-panel">

            <div className="panel-header">

              <div>

                <p className="section-label">
                  EXECUTION
                </p>

                <h2>
                  Razorpay test execution
                </h2>

              </div>

              <span className="live-badge test-mode-badge">
                <span></span>
                TEST MODE
              </span>

            </div>


            <div className="execution-card">

              <div className="execution-icon">
                ✓
              </div>

              <div>

                <strong>
                  {summary.successful_executions > 0
                    ? "Payment Link created"
                    : "No test execution yet"}
                </strong>

                <p>
                  A policy-approved recovery decision was executed
                  through the Razorpay Test Mode payment-link API.
                  Execution is recorded in the audit trail for traceability.
                </p>

              </div>

            </div>


            <div className="execution-stats">

              <div>
                <span>
                  Test interventions
                </span>

                <strong>
                  {summary.test_interventions}
                </strong>
              </div>


              <div>
                <span>
                  Successful
                </span>

                <strong>
                  {summary.successful_executions}
                </strong>
              </div>


              <div>
                <span>
                  Failed
                </span>

                <strong>
                  {summary.failed_executions}
                </strong>
              </div>

            </div>


            <div className="execution-value">

              <span>
                EXECUTED TRANSACTION VALUE
              </span>

              <strong>
                {formatINR(
                  summary.test_transaction_value
                )}
              </strong>

            </div>


            <div className="architecture">

              <span>AI</span>

              <i>→</i>

              <span>POLICY</span>

              <i>→</i>

              <span>RAZORPAY</span>

            </div>

          </div>

        </section>


        {/* =====================================================
            PRIORITIZED QUEUE
        ===================================================== */}

        <section className="panel opportunities-panel">

          <div className="panel-header">

            <div>

              <p className="section-label">
                PRIORITIZED QUEUE
              </p>

              <h2>
                Highest-value recovery opportunities
              </h2>

              <p className="queue-subtitle">
                Ranked by expected recoverable revenue:
                amount at risk × recovery probability.
              </p><div className="opportunity-filters">
                <input
                  type="text"
                  placeholder="Search transaction ID..."
                  value={opportunitySearch}
                  onChange={(e) =>
                    setOpportunitySearch(e.target.value)
                  }
                  className="opportunity-search"
                />

                <select
                  value={opportunityAction}
                  onChange={(e) =>
                    setOpportunityAction(e.target.value)
                  }
                  className="opportunity-filter"
                >
                  <option value="ALL">All strategies</option>
                  <option value="PAYMENT_LINK">Payment Link</option>
                  <option value="RETRY">Retry</option>
                  <option value="REMINDER">Reminder</option>
                  <option value="ESCALATE">Escalate</option>
                  <option value="STOP">Stop</option>
                </select>

                <select
                  value={opportunityStatus}
                  onChange={(e) =>
                    setOpportunityStatus(e.target.value)
                  }
                  className="opportunity-filter"
                >
                  <option value="ALL">All statuses</option>
                  <option value="ABANDONED">Abandoned</option>
                  <option value="FAILED">Failed</option>
                </select>

                <select
                  value={opportunityHumanReview}
                  onChange={(e) =>
                    setOpportunityHumanReview(e.target.value)
                  }
                  className="opportunity-filter"
                >
                  <option value="ALL">All review states</option>
                  <option value="REQUIRED">Human review</option>
                  <option value="NOT_REQUIRED">No human review</option>
                </select>
              </div>

              <div className="opportunity-result-count">
                Showing {filteredOpportunities.length} of{" "}
                {opportunities.length} opportunities
              </div>

            </div>


            <span className="panel-count">
              Highest expected recovery
            </span>

          </div>


          <div className="table-wrapper">

            <table>

              <thead>

                <tr>

                  <th>
                    Priority
                  </th>

                  <th>
                    Transaction
                  </th>

                  <th>
                    Status
                  </th>

                  <th>
                    Amount
                  </th>

                  <th>
                    Recovery probability
                  </th>

                  <th>
                    Expected recovery
                  </th>

                  <th>
                    Recommended action
                  </th>

                </tr>

              </thead>


              <tbody>

                {filteredOpportunities.map((item) => (

                  <tr
                    key={item.transaction_id}
                    className={`opportunity-row ${selectedTransaction?.transaction_id === item.transaction_id
                      ? "selected-opportunity"
                      : ""
                      }`}
                    onClick={() =>
                      openRecoveryConsole(
                        item.transaction_id
                      )
                    }
                  >

                    <td>

                      <span className="priority-rank">
                        #{item.priority_rank}
                      </span>

                    </td>


                    <td>

                      <span className="transaction-id">
                        {item.transaction_id}
                      </span>

                    </td>


                    <td>

                      <span
                        className={`status-pill ${String(
                          item.payment_status
                        ).toLowerCase()}`}
                      >
                        {item.payment_status}
                      </span>

                    </td>


                    <td className="amount">
                      {formatINR(item.amount)}
                    </td>


                    <td>

                      <div className="probability">

                        {(
                          Number(
                            item.recovery_probability
                          ) * 100
                        ).toFixed(2)}
                        %

                      </div>

                    </td>


                    <td className="expected-recovery">
                      {formatINR(
                        item.expected_recovery
                      )}
                    </td>


                    <td>

                      <span
                        className={`decision-pill ${String(
                          item.recommended_action
                        )
                          .toLowerCase()
                          .replaceAll(
                            "_",
                            "-"
                          )
                          .replaceAll(
                            " ",
                            "-"
                          )}`}
                      >

                        {String(
                          item.recommended_action
                        ).replaceAll(
                          "_",
                          " "
                        )}

                      </span>

                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          </div>

        </section>


        {/* =====================================================
            RECOVERY CONSOLE
        ===================================================== */}

        {selectedTransaction && (

          <section
            className="panel recovery-console"
            id="recovery-console"
          >

            <div className="console-header">

              <div className="console-title-block">

                <div className="console-open-indicator">
                  <span className="console-status-dot"></span>
                  RECOVERY CONSOLE OPEN
                </div>

                <h2>
                  {selectedTransaction.transaction_id}
                </h2>

                <p className="console-subtitle">
                  Review AI decision, policy controls, and recovery execution
                </p>

              </div>

              <button
                type="button"
                className="close-console"
                onClick={() => setSelectedTransaction(null)}
                aria-label="Close recovery console"
              >
                <span className="close-console-icon">×</span>
                <span>Close Console</span>
              </button>

            </div>


            {recoveryLoading && (

              <div className="console-loading">
                Loading recovery decision...
              </div>

            )}


            {recoveryError && (

              <div className="console-error">
                {recoveryError}
              </div>

            )}


            {!recoveryLoading &&
              !recoveryError && (
                <>

                  <div className="recovery-overview">

                    <div>

                      <span>
                        Transaction amount
                      </span>

                      <strong>
                        {formatINR(
                          selectedTransaction.amount
                        )}
                      </strong>

                    </div>


                    <div>

                      <span>
                        Recovery probability
                      </span>

                      <strong>
                        {(
                          selectedTransaction
                            .recovery_probability *
                          100
                        ).toFixed(2)}
                        %
                      </strong>

                    </div>


                    <div>

                      <span>
                        Expected recovery
                      </span>

                      <strong>
                        {formatINR(
                          selectedTransaction
                            .expected_recovery
                        )}
                      </strong>

                    </div>

                  </div>


                  <div className="console-grid">

                    <div className="console-card">

                      <span className="console-label">
                        PAYMENT STATUS
                      </span>

                      <strong>
                        {
                          selectedTransaction.payment_status
                        }
                      </strong>

                      <small>
                        Failure reason:{" "}
                        {
                          selectedTransaction.failure_reason
                        }
                      </small>

                      <small>
                        Retry count:{" "}
                        {
                          selectedTransaction.retry_count
                        }
                      </small>

                    </div>


                    <div className="console-card diagnosis-card">

                      <span className="console-label">
                        AI DIAGNOSIS
                      </span>

                      <p>
                        {
                          selectedTransaction.diagnosis
                        }
                      </p>

                    </div>

                  </div>


                  <div className="decision-flow">

                    <div className="flow-step">

                      <span>
                        AI
                      </span>

                      <strong>
                        {
                          selectedTransaction.recommended_action
                        }
                      </strong>

                    </div>


                    <div className="flow-arrow">
                      →
                    </div>


                    <div className="flow-step">

                      <span>
                        POLICY
                      </span>

                      <strong>
                        {
                          selectedTransaction.policy_approved
                            ? "APPROVED"
                            : "BLOCKED"
                        }
                      </strong>

                    </div>


                    <div className="flow-arrow">
                      →
                    </div>


                    <div className="flow-step">

                      <span>
                        HUMAN REVIEW
                      </span>

                      <strong>
                        {
                          selectedTransaction.requires_human
                            ? "REQUIRED"
                            : "NOT REQUIRED"
                        }
                      </strong>

                    </div>

                  </div>


                  <div className="policy-result">

                    <span className="console-label">
                      POLICY REASON
                    </span>

                    <p>
                      {
                        selectedTransaction.policy_reason
                      }
                    </p>

                  </div>

                  {/* =====================================================
                      DECISION EVIDENCE
                  ===================================================== */}

                  <div className="decision-evidence">

                    <div className="decision-evidence-header">
                      <div>
                        <span className="console-label">
                          DECISION EVIDENCE
                        </span>

                        <h3>
                          Why RecoverAI chose this action
                        </h3>

                        <p>
                          The decision combines recovery probability,
                          transaction value, expected recovery, and
                          policy constraints.
                        </p>
                      </div>

                      <span className="evidence-badge">
                        AI DECISION
                      </span>
                    </div>


                    <div className="evidence-grid">

                      <div className="evidence-card">
                        <span className="console-label">
                          RECOVERY PROBABILITY
                        </span>

                        <strong>
                          {(
                            Number(
                              selectedTransaction.recovery_probability
                            ) * 100
                          ).toFixed(2)}
                          %
                        </strong>

                        <small>
                          Estimated probability of successful recovery
                        </small>
                      </div>


                      <div className="evidence-card">
                        <span className="console-label">
                          EXPECTED RECOVERY
                        </span>

                        <strong>
                          {formatINR(
                            selectedTransaction.expected_recovery
                          )}
                        </strong>

                        <small>
                          Probability-weighted recoverable value
                        </small>
                      </div>


                      <div className="evidence-card">
                        <span className="console-label">
                          PRIORITY SCORE
                        </span>

                        <strong>
                          {formatINR(
                            selectedTransaction.priority_score ??
                            selectedTransaction.expected_recovery
                          )}
                        </strong>

                        <small>
                          Expected value used for opportunity prioritization
                        </small>
                      </div>


                      <div className="evidence-card">
                        <span className="console-label">
                          RISK LEVEL
                        </span>

                        <strong>
                          {
                            selectedTransaction.risk_level ||
                            "—"
                          }
                        </strong>

                        <small>
                          Policy risk classification
                        </small>
                      </div>

                    </div>


                    <div className="evidence-rationale">

                      <div>
                        <span className="console-label">
                          MODEL RATIONALE
                        </span>

                        <p>
                          {
                            selectedTransaction.diagnosis
                          }
                        </p>
                      </div>


                      <div>
                        <span className="console-label">
                          POLICY RATIONALE
                        </span>

                        <p>
                          {
                            selectedTransaction.policy_reason
                          }
                        </p>
                      </div>

                    </div>

                  </div>

                  {/* =====================================================
    AI DECISION PATH
===================================================== */}
                  <div className="decision-path">

                    <div className="decision-path-header">
                      <div>
                        <span className="console-label">
                          AI DECISION PATH
                        </span>

                        <h4>
                          From transaction signal to governed recovery action
                        </h4>

                        <p className="decision-path-description">
                          RecoverAI evaluates the transaction, predicts recovery potential,
                          applies policy controls, and selects the safest recovery action.
                        </p>
                      </div>

                      <span className="evidence-badge">
                        POLICY-GOVERNED AI
                      </span>
                    </div>


                    <div className="decision-flow">

                      {/* STEP 01 */}
                      <div className="decision-node">

                        <div className="decision-node-top">
                          <span className="decision-step-number">
                            01
                          </span>

                          <span className="decision-node-type">
                            SIGNAL
                          </span>
                        </div>

                        <div className="decision-node-content">

                          <strong>
                            TRANSACTION SIGNAL
                          </strong>

                          <p>
                            {selectedTransaction.payment_status === "abandoned"
                              ? "Checkout abandonment detected."
                              : `Payment failure detected: ${selectedTransaction.failure_reason ||
                              "unknown reason"
                              }.`
                            }
                          </p>

                          <span className="decision-node-value">
                            {String(
                              selectedTransaction.payment_status
                            ).toUpperCase()}
                          </span>

                        </div>

                      </div>


                      <div className="decision-connector">
                        <span>→</span>
                      </div>


                      {/* STEP 02 */}
                      <div className="decision-node decision-node-ai">

                        <div className="decision-node-top">
                          <span className="decision-step-number">
                            02
                          </span>

                          <span className="decision-node-type">
                            MODEL
                          </span>
                        </div>

                        <div className="decision-node-content">

                          <strong>
                            AI PREDICTION
                          </strong>

                          <p>
                            Recovery probability and expected recoverable
                            value estimated from transaction signals.
                          </p>

                          <div className="decision-metrics">

                            <div>
                              <span>RECOVERY</span>

                              <strong>
                                {(
                                  Number(
                                    selectedTransaction.recovery_probability
                                  ) * 100
                                ).toFixed(2)}
                                %
                              </strong>
                            </div>

                            <div>
                              <span>EXPECTED</span>

                              <strong>
                                {formatINR(
                                  selectedTransaction.expected_recovery
                                )}
                              </strong>
                            </div>

                          </div>

                        </div>

                      </div>


                      <div className="decision-connector">
                        <span>→</span>
                      </div>


                      {/* STEP 03 */}
                      <div className="decision-node decision-node-policy">

                        <div className="decision-node-top">
                          <span className="decision-step-number">
                            03
                          </span>

                          <span className="decision-node-type">
                            GOVERNANCE
                          </span>
                        </div>

                        <div className="decision-node-content">

                          <strong>
                            POLICY GATE
                          </strong>

                          <p>
                            {selectedTransaction.requires_human
                              ? "Human review is required before automated recovery."
                              : selectedTransaction.policy_approved
                                ? "Policy approved this recovery strategy for execution."
                                : "Policy blocked automated execution."
                            }
                          </p>

                          <span
                            className={`decision-policy-status ${selectedTransaction.requires_human
                              ? "review"
                              : selectedTransaction.policy_approved
                                ? "approved"
                                : "blocked"
                              }`}
                          >
                            {selectedTransaction.requires_human
                              ? "HUMAN REVIEW"
                              : selectedTransaction.policy_approved
                                ? "✓ APPROVED"
                                : "✕ BLOCKED"
                            }
                          </span>

                        </div>

                      </div>


                      <div className="decision-connector">
                        <span>→</span>
                      </div>


                      {/* STEP 04 */}
                      <div className="decision-node decision-node-action">

                        <div className="decision-node-top">
                          <span className="decision-step-number">
                            04
                          </span>

                          <span className="decision-node-type">
                            OUTCOME
                          </span>
                        </div>

                        <div className="decision-node-content">

                          <strong>
                            FINAL ACTION
                          </strong>

                          <p>
                            RecoverAI selects the recommended recovery
                            strategy based on the model and policy decision.
                          </p>

                          <span className="decision-action-value">
                            {String(
                              selectedTransaction.recommended_action
                            ).replaceAll("_", " ")}
                          </span>

                        </div>

                      </div>

                    </div>


                    {/* Decision summary */}
                    <div className="decision-path-summary">

                      <span className="console-label">
                        DECISION OUTCOME
                      </span>

                      <div className="decision-summary-content">

                        <span className="decision-summary-flow">
                          SIGNAL
                          <span>→</span>
                          PREDICTION
                          <span>→</span>
                          POLICY
                          <span>→</span>
                          ACTION
                        </span>

                        <strong>
                          {selectedTransaction.recommended_action}
                        </strong>

                      </div>

                    </div>

                  </div>

                  <div className="execution-result">

                    <div className="execution-status-card">

                      <span className="console-label">
                        EXECUTION STATUS
                      </span>

                      <strong>
                        {selectedTransaction.execution_status}
                      </strong>

                    </div>


                    {existingExecution && (

                      <div className="existing-execution">

                        <div className="execution-evidence-header">

                          <div>

                            <span className="console-label">
                              RAZORPAY TEST MODE
                            </span>

                            <strong>
                              PAYMENT LINK CREATED
                            </strong>

                            <small>
                              Policy-approved recovery was successfully
                              executed through the Razorpay payment-link flow.
                            </small>

                          </div>

                          <span className="execution-success-badge">
                            ✓ EXECUTED
                          </span>

                        </div>


                        <div className="execution-evidence-grid">

                          <div>

                            <span className="console-label">
                              TRANSACTION
                            </span>

                            <strong>
                              {existingExecution.transaction_id}
                            </strong>

                          </div>


                          <div>

                            <span className="console-label">
                              ACTION
                            </span>

                            <strong>
                              {String(
                                existingExecution.action
                              ).replaceAll("_", " ")}
                            </strong>

                          </div>


                          <div>

                            <span className="console-label">
                              AMOUNT
                            </span>

                            <strong>
                              {formatINR(
                                existingExecution.amount_inr
                              )}
                            </strong>

                          </div>


                          <div>

                            <span className="console-label">
                              PAYMENT LINK ID
                            </span>

                            <strong>
                              {
                                existingExecution
                                  .razorpay_payment_link_id
                              }
                            </strong>

                          </div>

                        </div>


                        <div className="execution-link-row">

                          <div>

                            <span className="console-label">
                              RAZORPAY PAYMENT LINK
                            </span>

                            <small>
                              Test-mode recovery payment link generated
                              for this transaction.
                            </small>

                          </div>

                          <a
                            href={
                              existingExecution.short_url
                            }
                            target="_blank"
                            rel="noreferrer"
                            className="execution-link-button"
                          >
                            Open Test Payment Link →
                          </a>

                        </div>

                      </div>

                    )}
                    {/* =================================================
                        EXECUTION CONTROL
                    ================================================= */}

                    {selectedTransaction.recommended_action ===
                      "PAYMENT_LINK" &&
                      selectedTransaction.policy_approved &&
                      !selectedTransaction.requires_human &&
                      !existingExecution && (
                        <div className="execution-control">
                          <div className="execution-control-copy">
                            <span className="console-label">
                              CONTROLLED EXECUTION
                            </span>

                            <strong>
                              Ready for Razorpay Test Mode
                            </strong>

                            <small>
                              Policy-approved payment-link recovery.
                              No automatic customer charge is performed.
                            </small>
                          </div>

                          <button
                            type="button"
                            className="execute-recovery-button"
                            onClick={() =>
                              executeRecovery(
                                selectedTransaction.transaction_id
                              )
                            }
                            disabled={executionLoading}
                          >
                            {executionLoading
                              ? "Executing..."
                              : "Execute Recovery →"}
                          </button>
                        </div>
                      )}

                    {recoveryError && (
                      <div className="recovery-execution-error">
                        <strong>
                          Execution failed
                        </strong>

                        <span>
                          {recoveryError}
                        </span>
                      </div>
                    )}
                    <div>

                      <span className="console-label">
                        RECOMMENDED ACTION
                      </span>

                      <strong>
                        {
                          selectedTransaction.recommended_action
                        }
                      </strong>

                    </div>

                  </div>

                </>
              )}

          </section>

        )}


        {/* =====================================================
            AUDIT TRAIL
        ===================================================== */}

        <section className="panel audit-panel">

          <div className="panel-header">

            <div>

              <p className="section-label">
                AUDIT TRAIL
              </p>

              <h2>
                Recent execution history
              </h2>

            </div>

            <span className="panel-count">
              {executions.length}{" "}
              audit events
            </span>

          </div>


          {executions.length === 0 ? (

            <div className="empty-state">
              No execution records yet.
            </div>

          ) : (

            <div className="audit-table">

              {executions.map(
                (execution, index) => (

                  <div
                    className="audit-row"
                    key={`${execution.transaction_id}-${index}`}
                    onClick={() =>
                      openRecoveryConsole(
                        execution.transaction_id
                      )
                    }
                  >

                    <div>

                      <strong>
                        {
                          execution.transaction_id
                        }
                      </strong>

                      <small>
                        {
                          execution.action
                        }
                      </small>

                    </div>


                    <div>

                      <span>
                        {formatINR(
                          execution.amount_inr
                        )}
                      </span>

                    </div>


                    <div>

                      <span
                        className={`execution-status ${String(
                          execution.execution_status
                        ).toLowerCase()}`}
                      >
                        {
                          execution.execution_status
                        }
                      </span>

                    </div>

                  </div>

                )
              )}

            </div>

          )}

        </section>


        {/* =====================================================
            AUDIT STRIP
        ===================================================== */}

        <section className="audit-strip">

          <div>

            <span className="audit-icon">
              ✓
            </span>

            <div>

              <strong>
                Audit trail active
              </strong>

              <p>
                Every AI recommendation, policy
                decision and execution outcome is
                recorded.
              </p>

            </div>

          </div>


          <div className="audit-values">

            <span>
              {summary.total_transactions.toLocaleString()}{" "}
              analyzed
            </span>

            <span>
              {
                summary.recovery_opportunities.toLocaleString()
              }{" "}
              opportunities
            </span>

            <span>
              {
                summary.human_escalations.toLocaleString()
              }{" "}
              escalated
            </span>

          </div>

        </section>

      </main>

    </div >
  );
}


function MetricCard({
  label,
  value,
  description,
}) {
  return (
    <div className="metric-card">

      <span className="metric-label">
        {label}
      </span>

      <strong className="metric-value">
        {value}
      </strong>

      <span className="metric-description">
        {description}
      </span>

    </div>
  );
}


export default App;