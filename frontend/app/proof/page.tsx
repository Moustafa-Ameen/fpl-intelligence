"use client";

import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { EmptyState, ErrorState, LoadingState } from "@/components/LoadingState";
import { Panel } from "@/components/Panel";
import { SectionHeader } from "@/components/SectionHeader";
import { getAccuracy, getCaptaincyBacktest, getTop10Metrics } from "@/lib/api";
import { points } from "@/lib/format";
import type { AccuracyResult, BacktestResult, Top10Metric } from "@/lib/types";

export default function ProofPage() {
  const [accuracy, setAccuracy] = useState<AccuracyResult[]>([]);
  const [captaincy, setCaptaincy] = useState<BacktestResult[]>([]);
  const [top10, setTop10] = useState<Top10Metric[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    Promise.all([getAccuracy(), getCaptaincyBacktest(), getTop10Metrics()])
      .then(([accuracyRows, captaincyRows, top10Rows]) => {
        setAccuracy(accuracyRows);
        setCaptaincy(captaincyRows);
        setTop10(top10Rows);
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState />;
  if (!accuracy.length) return <EmptyState />;

  const bestRaw = Math.min(...accuracy.map((row) => row.raw_MAE));
  const bestAdjusted = Math.min(...accuracy.map((row) => row.adjusted_MAE));

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Does the model actually work?"
        subtitle="We tested it across the full 2025-26 season. Here's the evidence."
      />

      <Panel title="Accuracy">
        <div className="grid grid-cols-2 gap-6">
          <AccuracyTable
            title="Raw predictions"
            rows={accuracy}
            best={bestRaw}
            columns={["raw_MAE", "raw_RMSE"]}
          />
          <AccuracyTable
            title="Minutes-adjusted predictions"
            rows={accuracy}
            best={bestAdjusted}
            columns={["adjusted_MAE", "adjusted_RMSE"]}
          />
        </div>
      </Panel>

      <Panel title="Captaincy Backtest">
        <div className="mb-5 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-muted">
              <tr>
                <th className="pb-3">Strategy</th>
                <th className="pb-3">Total Captain Points</th>
                <th className="pb-3">Avg Per GW</th>
              </tr>
            </thead>
            <tbody>
              {captaincy.map((row) => (
                <tr key={row.strategy} className="border-b border-border-muted">
                  <td className="py-3 text-primary">{row.strategy}</td>
                  <td className="py-3 font-mono text-primary">{points(row.total_captain_points, 0)}</td>
                  <td className="py-3 font-mono text-primary">{points(row.avg_per_gameweek)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={captaincy}>
              <CartesianGrid stroke="#1F2231" />
              <XAxis dataKey="strategy" stroke="#94A3B8" tick={{ fontSize: 11 }} interval={0} angle={-18} height={70} />
              <YAxis stroke="#94A3B8" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#161616", border: "1px solid #2A2A2A", color: "#FFFFFF" }} />
              <Bar dataKey="total_captain_points" fill="#00FF87" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Panel>

      <Panel title="Top-10 Accuracy">
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={top10}>
              <CartesianGrid stroke="#1F2231" />
              <XAxis dataKey="model" stroke="#94A3B8" tick={{ fontSize: 11 }} interval={0} angle={-12} height={60} />
              <YAxis stroke="#94A3B8" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#161616", border: "1px solid #2A2A2A", color: "#FFFFFF" }} />
              <Legend />
              <Bar dataKey="precision_at_10" name="Precision @10" fill="#00FF87" />
              <Bar dataKey="recall_at_10" name="Recall @10" fill="#10B981" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <p className="mt-4 text-sm text-muted">
          Precision: of our top 10 picks each week, how many were actually top scorers.
          Recall: of the actual top 10 scorers, how many did we predict.
        </p>
      </Panel>

      <div className="rounded-xl border border-border-muted border-l-cyan bg-card p-5 text-sm leading-6 text-primary">
        Our model beat a no-ML baseline on both accuracy and captaincy points across the full 2025-26
        season. The minutes adjustment improved typical predictions but occasionally over-penalised
        reliable starters. One season of backtest data — treat this as strong evidence, not a
        guarantee.
      </div>
    </div>
  );
}

function AccuracyTable({
  title,
  rows,
  best,
  columns,
}: {
  title: string;
  rows: AccuracyResult[];
  best: number;
  columns: ["raw_MAE", "raw_RMSE"] | ["adjusted_MAE", "adjusted_RMSE"];
}) {
  return (
    <div>
      <h3 className="mb-3 text-sm font-semibold text-primary">{title}</h3>
      <table className="w-full text-left text-sm">
        <thead className="text-xs uppercase text-muted">
          <tr>
            <th className="pb-3">Model</th>
            <th className="pb-3">MAE</th>
            <th className="pb-3">RMSE</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={`${title}-${row.model}`}
              className={`border-b border-border-muted ${row[columns[0]] === best ? "border-l-4 border-l-cyan" : ""}`}
            >
              <td className="py-3 pl-3 text-primary">{row.model}</td>
              <td className="py-3 font-mono text-primary">{points(row[columns[0]])}</td>
              <td className="py-3 font-mono text-primary">{points(row[columns[1]])}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
