/** @odoo-module **/
/**
 * FleetFlow — Analytics & Financial Reports (Odoo 18 OWL Component)
 *
 * Sections:
 *   1. KPI row: Total Fuel Cost | Fleet ROI | Utilization Rate
 *   2. Charts: Fuel Efficiency Trend (SVG line) | Top 5 Costliest Vehicles (SVG bar)
 *   3. Financial Summary of Month table (Month | Revenue | Fuel Cost | Maintenance | Net Profit)
 *   4. Dead Stock Alerts (idle vehicles)
 *   5. One-click CSV export
 */

import { Component, useState, onWillStart, useRef, onMounted, markup } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// ── SVG Chart Helpers ──────────────────────────────────────────────────────

function makeSVGLine(points, width, height, color = "#7c3aed", fillColor = null) {
    if (!points || points.length < 2) return "";
    const maxY = Math.max(...points.map((p) => p.y), 1);
    const minY = Math.min(...points.map((p) => p.y), 0);
    const rangeY = maxY - minY || 1;
    const padT = 18, padB = 28, padL = 44, padR = 12;
    const w = width - padL - padR;
    const h = height - padT - padB;

    const px = (i) => padL + (i / (points.length - 1)) * w;
    const py = (v) => padT + h - ((v - minY) / rangeY) * h;

    const pathD = points
        .map((p, i) => `${i === 0 ? "M" : "L"} ${px(i).toFixed(1)} ${py(p.y).toFixed(1)}`)
        .join(" ");

    let fill = "";
    if (fillColor) {
        const firstX = px(0), lastX = px(points.length - 1);
        const bottomY = py(minY) + 1;
        fill = `<path d="${pathD} L ${lastX} ${bottomY} L ${firstX} ${bottomY} Z"
                     fill="${fillColor}" opacity="0.12"/>`;
    }

    // Grid lines
    const gridLines = [0, 0.25, 0.5, 0.75, 1].map((ratio) => {
        const v = minY + rangeY * ratio;
        const y = py(v).toFixed(1);
        const label = v >= 1000 ? `${(v / 1000).toFixed(1)}k` : v.toFixed(1);
        return `<line x1="${padL}" y1="${y}" x2="${padL + w}" y2="${y}"
                      stroke="#e2e8f0" stroke-width="1"/>
                <text x="${padL - 4}" y="${parseFloat(y) + 3}" text-anchor="end"
                      font-size="9" fill="#94a3b8">${label}</text>`;
    }).join("");

    // X labels
    const xLabels = points.map((p, i) => {
        const x = px(i).toFixed(1);
        return `<text x="${x}" y="${height - 6}" text-anchor="middle"
                     font-size="9" fill="#94a3b8">${p.label || i}</text>`;
    }).join("");

    // Data points
    const dots = points.map((p, i) =>
        `<circle cx="${px(i).toFixed(1)}" cy="${py(p.y).toFixed(1)}" r="3.5"
                 fill="${color}" stroke="#fff" stroke-width="1.5">
           <title>${p.label}: ${p.y.toFixed(2)}</title>
         </circle>`
    ).join("");

    return `<svg width="100%" height="${height}" viewBox="0 0 ${width} ${height}"
                 preserveAspectRatio="xMidYMid meet" style="overflow:visible">
        ${gridLines}
        ${fill}
        <path d="${pathD}" stroke="${color}" stroke-width="2.5" fill="none" stroke-linejoin="round"/>
        ${dots}
        ${xLabels}
    </svg>`;
}

function makeSVGBar(bars, width, height) {
    if (!bars || bars.length === 0) return "";
    const maxY = Math.max(...bars.map((b) => b.value), 1);
    const padT = 18, padB = 36, padL = 48, padR = 12;
    const w = width - padL - padR;
    const h = height - padT - padB;
    const barW = Math.max(8, (w / bars.length) * 0.55);
    const gap = w / bars.length;

    const colors = ["#7c3aed", "#3b82f6", "#10b981", "#f59e0b", "#ef4444",
                    "#8b5cf6", "#06b6d4", "#84cc16"];

    // Grid
    const gridLines = [0, 0.5, 1].map((r) => {
        const v = maxY * r;
        const y = (padT + h - r * h).toFixed(1);
        const label = v >= 100000 ? `${(v / 100000).toFixed(1)}L`
                    : v >= 1000  ? `${(v / 1000).toFixed(1)}k`
                    : v.toFixed(0);
        return `<line x1="${padL}" y1="${y}" x2="${padL + w}" y2="${y}"
                      stroke="#e2e8f0" stroke-width="1"/>
                <text x="${padL - 5}" y="${parseFloat(y) + 3}" text-anchor="end"
                      font-size="9" fill="#94a3b8">${label}</text>`;
    }).join("");

    const rects = bars.map((b, i) => {
        const barH = Math.max(2, (b.value / maxY) * h);
        const x = (padL + i * gap + (gap - barW) / 2).toFixed(1);
        const y = (padT + h - barH).toFixed(1);
        const color = colors[i % colors.length];
        const shortLabel = b.label.length > 7 ? b.label.slice(0, 7) : b.label;
        return `<rect x="${x}" y="${y}" width="${barW}" height="${barH.toFixed(1)}"
                      rx="4" fill="${color}" opacity="0.88">
                  <title>${b.label}: ${b.value.toFixed(2)}</title>
                </rect>
                <text x="${parseFloat(x) + barW / 2}" y="${height - 8}"
                      text-anchor="middle" font-size="9" fill="#64748b">${shortLabel}</text>`;
    }).join("");

    return `<svg width="100%" height="${height}" viewBox="0 0 ${width} ${height}"
                 preserveAspectRatio="xMidYMid meet" style="overflow:visible">
        ${gridLines}
        ${rects}
        <line x1="${padL}" y1="${padT}" x2="${padL}" y2="${padT + h}"
              stroke="#cbd5e1" stroke-width="1"/>
        <line x1="${padL}" y1="${padT + h}" x2="${padL + w}" y2="${padT + h}"
              stroke="#cbd5e1" stroke-width="1"/>
    </svg>`;
}

// ── Main Component ─────────────────────────────────────────────────────────

export class FleetFlowAnalytics extends Component {
    static template = "fleetflow.Analytics";
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            // KPIs
            totalFuelCost: 0,
            fleetROI: 0,
            utilizationRate: 0,
            totalRevenue: 0,
            totalMaintenance: 0,
            netProfit: 0,
            // Charts data
            efficiencyChartSVG: "",
            topCostlySVG: "",
            // Financial table
            monthlySummary: [],
            // Dead stock
            deadStockVehicles: [],
            // UI
            loading: true,
            activeTab: "overview",          // overview | monthly | deadstock
            selectedYear: new Date().getFullYear(),
        });

        onWillStart(async () => {
            console.log("Loading analytics data...");
            await this._loadAll();
        });
    }

    // ── Data Loading ────────────────────────────────────────────────────────

    async _loadAll() {
        this.state.loading = true;
        try {
            await Promise.all([
                this._loadKPIs(),
                this._loadEfficiencyChart(),
                this._loadTopCostlyChart(),
                this._loadMonthlySummary(),
                this._loadDeadStock(),
            ]);
        } finally {
            this.state.loading = false;
        }
    }

    async _loadKPIs() {
        // Aggregate from ff.vehicle computed fields
        const vehicles = await this.orm.searchRead(
            "ff.vehicle",
            [["active", "=", true], ["state", "!=", "retired"]],
            ["state", "total_fuel_cost", "total_maintenance_cost",
             "total_revenue", "vehicle_roi", "total_operational_cost"]
        );

        const totalFuel   = vehicles.reduce((s, v) => s + v.total_fuel_cost, 0);
        const totalMaint  = vehicles.reduce((s, v) => s + v.total_maintenance_cost, 0);
        const totalRev    = vehicles.reduce((s, v) => s + v.total_revenue, 0);
        const totalOp     = vehicles.reduce((s, v) => s + v.total_operational_cost, 0);
        const avgROI      = vehicles.length
            ? vehicles.reduce((s, v) => s + v.vehicle_roi, 0) / vehicles.length
            : 0;

        const onTrip      = vehicles.filter((v) => v.state === "on_trip").length;
        const total       = vehicles.length || 1;
        const utilRate    = Math.round((onTrip / total) * 100);

        this.state.totalFuelCost    = totalFuel;
        this.state.fleetROI         = avgROI;
        this.state.utilizationRate  = utilRate;
        this.state.totalRevenue     = totalRev;
        this.state.totalMaintenance = totalMaint;
        this.state.netProfit        = totalRev - totalOp;
    }

    async _loadEfficiencyChart() {
        // Get per-vehicle fuel efficiency, build line-like data sorted by vehicle name
        const vehicles = await this.orm.searchRead(
            "ff.vehicle",
            [["active", "=", true], ["fuel_efficiency", ">", 0]],
            ["name", "fuel_efficiency"],
            { order: "name asc", limit: 12 }
        );

        const points = vehicles.map((v) => ({
            label: v.name.length > 8 ? v.name.slice(0, 8) : v.name,
            y: v.fuel_efficiency,
        }));

        this.state.efficiencyChartSVG = points.length >= 2
            ? markup(makeSVGLine(points, 420, 180, "#7c3aed", "#7c3aed"))
            : "<p class='ff-chart-empty'>No fuel efficiency data yet.</p>";
    }

    async _loadTopCostlyChart() {
        // Top 5 vehicles by total operational cost
        const vehicles = await this.orm.searchRead(
            "ff.vehicle",
            [["active", "=", true], ["total_operational_cost", ">", 0]],
            ["name", "total_operational_cost"],
            { order: "total_operational_cost desc", limit: 5 }
        );

        const bars = vehicles.map((v) => ({
            label: v.name,
            value: v.total_operational_cost,
        }));

        this.state.topCostlySVG = bars.length > 0
            ? markup(makeSVGBar(bars, 420, 180))
            : "<p class='ff-chart-empty'>No expense data yet.</p>";
    }

    async _loadMonthlySummary() {
        // Get all completed trips grouped by month for revenue
        const trips = await this.orm.searchRead(
            "ff.trip",
            [["state", "=", "completed"]],
            ["scheduled_date", "revenue"]
        );

        // Get fuel expenses grouped by month
        const expenses = await this.orm.searchRead(
            "ff.fuel.expense",
            [],
            ["date", "cost", "expense_type"]
        );

        // Get maintenance by month
        const maint = await this.orm.searchRead(
            "ff.maintenance",
            [["state", "=", "done"]],
            ["service_date", "cost"]
        );

        // Build month map
        const months = {};

        const getKey = (dateStr) => {
            if (!dateStr) return null;
            const d = new Date(dateStr);
            return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
        };

        const monthLabel = (key) => {
            const [y, m] = key.split("-");
            return new Date(+y, +m - 1, 1).toLocaleString("en-IN", {
                month: "short", year: "2-digit"
            });
        };

        for (const t of trips) {
            const k = getKey(t.scheduled_date);
            if (!k) continue;
            if (!months[k]) months[k] = { revenue: 0, fuelCost: 0, maintenance: 0 };
            months[k].revenue += t.revenue || 0;
        }

        for (const e of expenses) {
            const k = getKey(e.date);
            if (!k) continue;
            if (!months[k]) months[k] = { revenue: 0, fuelCost: 0, maintenance: 0 };
            months[k].fuelCost += e.cost || 0;
        }

        for (const m of maint) {
            const k = getKey(m.service_date);
            if (!k) continue;
            if (!months[k]) months[k] = { revenue: 0, fuelCost: 0, maintenance: 0 };
            months[k].maintenance += m.cost || 0;
        }

        const sorted = Object.keys(months).sort().slice(-12); // last 12 months
        this.state.monthlySummary = sorted.map((k) => {
            const d = months[k];
            const netProfit = d.revenue - d.fuelCost - d.maintenance;
            return {
                key: k,
                label: monthLabel(k),
                revenue: d.revenue,
                fuelCost: d.fuelCost,
                maintenance: d.maintenance,
                netProfit,
            };
        }).reverse(); // newest first
    }

    async _loadDeadStock() {
        // Vehicles with available state and 0 trips in last 30 days
        const since = new Date();
        since.setDate(since.getDate() - 30);
        const sinceStr = since.toISOString().split("T")[0];

        const allVehicles = await this.orm.searchRead(
            "ff.vehicle",
            [["active", "=", true], ["state", "=", "available"]],
            ["name", "vehicle_type", "odometer", "trip_ids", "acquisition_date",
             "total_operational_cost", "total_revenue"]
        );

        // Find which ones had recent trips
        const recentTrips = await this.orm.searchRead(
            "ff.trip",
            [["scheduled_date", ">=", sinceStr + " 00:00:00"],
             ["state", "in", ["dispatched", "completed"]]],
            ["vehicle_id"]
        );
        const activeVehicleIds = new Set(recentTrips.map((t) => t.vehicle_id[0]));

        this.state.deadStockVehicles = allVehicles
            .filter((v) => !activeVehicleIds.has(v.id))
            .map((v) => ({
                id: v.id,
                name: v.name,
                type: v.vehicle_type,
                odometer: v.odometer,
                totalCost: v.total_operational_cost,
                totalRevenue: v.total_revenue,
                acquisitionDate: v.acquisition_date,
                daysSinceActivity: 30,
            }));
    }

    // ── Event Handlers ──────────────────────────────────────────────────────

    async onRefresh() {
        await this._loadAll();
        this.notification.add("Analytics refreshed", { type: "info" });
    }

    setTab = (tab) => {
        this.state.activeTab = tab;
    };

    async onVehicleClick(vehicleId) {
        await this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "ff.vehicle",
            res_id: vehicleId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    exportCSV() {
        const rows = [
            ["Month", "Revenue (Rs.)", "Fuel Cost (Rs.)", "Maintenance (Rs.)", "Net Profit (Rs.)"],
            ...this.state.monthlySummary.map((r) => [
                r.label,
                r.revenue.toFixed(2),
                r.fuelCost.toFixed(2),
                r.maintenance.toFixed(2),
                r.netProfit.toFixed(2),
            ]),
        ];

        const csv = rows.map((r) => r.map((c) => `"${c}"`).join(",")).join("\n");
        const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `fleetflow_financial_summary_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click();
        URL.revokeObjectURL(url);
        this.notification.add("CSV exported successfully!", { type: "success" });
    }

    exportDeadStockCSV() {
        const rows = [
            ["Vehicle", "Type", "Odometer (km)", "Total Cost (Rs.)", "Total Revenue (Rs.)", "Status"],
            ...this.state.deadStockVehicles.map((v) => [
                v.name, v.type, v.odometer.toFixed(0),
                v.totalCost.toFixed(2), v.totalRevenue.toFixed(2), "Idle 30+ days",
            ]),
        ];
        const csv = rows.map((r) => r.map((c) => `"${c}"`).join(",")).join("\n");
        const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `fleetflow_dead_stock_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click();
        URL.revokeObjectURL(url);
        this.notification.add("Dead Stock report exported!", { type: "success" });
    }

    // ── Formatters ──────────────────────────────────────────────────────────

    fmtCurrency(val) {
        if (!val && val !== 0) return "—";
        if (Math.abs(val) >= 100000)
            return `Rs. ${(val / 100000).toFixed(2)} L`;
        if (Math.abs(val) >= 1000)
            return `Rs. ${(val / 1000).toFixed(1)} K`;
        return `Rs. ${val.toFixed(0)}`;
    }

    fmtROI(val) {
        const sign = val >= 0 ? "+" : "";
        return `${sign}${val.toFixed(1)}%`;
    }

    getProfitClass(val) {
        if (val > 0) return "ff-profit-pos";
        if (val < 0) return "ff-profit-neg";
        return "ff-profit-zero";
    }
}

registry.category("actions").add("fleetflow_analytics", FleetFlowAnalytics);