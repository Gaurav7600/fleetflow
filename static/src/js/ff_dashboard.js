/** @odoo-module **/
/**
 * FleetFlow — Command Center Dashboard (Odoo 18 OWL Component)
 *
 * Displays:
 *   • KPI tiles: Active Fleet | Maintenance Alerts | Pending Cargo | Utilization Rate
 *   • Trip table with live search, group-by, filter, and sort
 *   • New Trip / New Vehicle quick-action buttons
 */

import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class FleetFlowDashboard extends Component {
    static template = "fleetflow.Dashboard";
    static props = {
        action: { type: Object, optional: true },
        actionId: { type: [Number, Boolean], optional: true },
        updateActionState: { type: Function, optional: true },
        className: { type: String, optional: true },
        globalState: { type: Object, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            // KPIs
            activeFleet: 0,
            maintenanceAlerts: 0,
            pendingCargo: 0,
            utilizationRate: 0,
            totalVehicles: 0,
            // Trip table
            trips: [],
            loading: true,
            // Search / filter
            searchQuery: "",
            filterStatus: "all",
            filterFleetType: "all",
            sortField: "scheduled_date",
            sortAsc: false,
        });

        onWillStart(async () => {
            await this._loadDashboardData();
        });
    }

    // ── Data Loading ──────────────────────────────────────────────────────────

    async _loadDashboardData() {
        this.state.loading = true;
        try {
            await Promise.all([
                this._loadKPIs(),
                this._loadTrips(),
            ]);
        } finally {
            this.state.loading = false;
        }
    }

    async _loadKPIs() {
        // Vehicle state counts
        const vehicleGroups = await this.orm.readGroup(
            "ff.vehicle",
            [["active", "=", true]],
            ["state"],
            ["state"]
        );

        let onTrip = 0, inShop = 0, available = 0, total = 0;
        for (const g of vehicleGroups) {
            total += g.state_count;
            if (g.state === "on_trip") onTrip = g.state_count;
            else if (g.state === "in_shop") inShop = g.state_count;
            else if (g.state === "available") available = g.state_count;
        }

        // Pending cargo = draft trips
        const pendingCargo = await this.orm.searchCount("ff.trip", [
            ["state", "=", "draft"],
        ]);

        // Utilization = on_trip / total active (excluding retired)
        const activeVehicles = onTrip + inShop + available;
        const utilRate = activeVehicles > 0
            ? Math.round((onTrip / activeVehicles) * 100)
            : 0;

        this.state.activeFleet = onTrip;
        this.state.maintenanceAlerts = inShop;
        this.state.pendingCargo = pendingCargo;
        this.state.utilizationRate = utilRate;
        this.state.totalVehicles = activeVehicles;
    }

    async _loadTrips() {
        // Build domain from filters
        const domain = this._buildDomain();

        const trips = await this.orm.searchRead(
            "ff.trip",
            domain,
            [
                "name", "vehicle_id", "fleet_type", "driver_id",
                "origin", "destination", "scheduled_date",
                "cargo_weight", "state",
            ],
            { limit: 80, order: `${this.state.sortField} ${this.state.sortAsc ? "asc" : "desc"}` }
        );

        this.state.trips = trips;
    }

    _buildDomain() {
        const domain = [];
        if (this.state.filterStatus !== "all") {
            domain.push(["state", "=", this.state.filterStatus]);
        }
        if (this.state.filterFleetType !== "all") {
            domain.push(["fleet_type", "=", this.state.filterFleetType]);
        }
        if (this.state.searchQuery.trim()) {
            const q = this.state.searchQuery.trim();
            domain.push("|", "|", "|",
                ["name", "ilike", q],
                ["vehicle_id.name", "ilike", q],
                ["driver_id.name", "ilike", q],
                ["destination", "ilike", q]
            );
        }
        return domain;
    }

    // ── Event Handlers ────────────────────────────────────────────────────────

    async onSearchInput(ev) {
        this.state.searchQuery = ev.target.value;
        await this._loadTrips();
    }

    async onFilterStatus(ev) {
        this.state.filterStatus = ev.target.value;
        await this._loadTrips();
    }

    async onFilterFleetType(ev) {
        this.state.filterFleetType = ev.target.value;
        await this._loadTrips();
    }

    async onSortChange(ev) {
        const field = ev.target.value;
        if (field === this.state.sortField) {
            this.state.sortAsc = !this.state.sortAsc;
        } else {
            this.state.sortField = field;
            this.state.sortAsc = true;
        }
        await this._loadTrips();
    }

    async onSortColumn(field) {
        if (field === this.state.sortField) {
            this.state.sortAsc = !this.state.sortAsc;
        } else {
            this.state.sortField = field;
            this.state.sortAsc = true;
        }
        await this._loadTrips();
    }

    async onNewTrip() {
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: "New Trip",
            res_model: "ff.trip",
            view_mode: "form",
            views: [[false, "form"]],
            target: "current",
            context: {},
        });
    }

    async onNewVehicle() {
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: "New Vehicle",
            res_model: "ff.vehicle",
            view_mode: "form",
            views: [[false, "form"]],
            target: "current",
            context: {},
        });
    }

    async onKpiClick(kpiType) {
        const actionMap = {
            active_fleet: {
                name: "Active Fleet (On Trip)",
                res_model: "ff.vehicle",
                domain: [["state", "=", "on_trip"]],
            },
            maintenance: {
                name: "Maintenance Alerts (In Shop)",
                res_model: "ff.vehicle",
                domain: [["state", "=", "in_shop"]],
            },
            pending_cargo: {
                name: "Pending Cargo (Draft Trips)",
                res_model: "ff.trip",
                domain: [["state", "=", "draft"]],
            },
        };

        const cfg = actionMap[kpiType];
        if (!cfg) return;

        await this.action.doAction({
            type: "ir.actions.act_window",
            name: cfg.name,
            res_model: cfg.res_model,
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain: cfg.domain,
            target: "current",
        });
    }

    async onTripClick(tripId) {
        await this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "ff.trip",
            res_id: tripId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    async onDispatch(ev, tripId) {
        ev.stopPropagation();
        try {
            await this.orm.call("ff.trip", "action_dispatch", [[tripId]]);
            this.notification.add("Trip dispatched successfully!", { type: "success" });
            await this._loadDashboardData();
        } catch (e) {
            this.notification.add(e.message || "Dispatch failed", { type: "danger" });
        }
    }

    async onComplete(ev, tripId) {
        ev.stopPropagation();
        try {
            await this.orm.call("ff.trip", "action_complete", [[tripId]]);
            this.notification.add("Trip completed!", { type: "success" });
            await this._loadDashboardData();
        } catch (e) {
            this.notification.add(e.message || "Could not complete trip", { type: "danger" });
        }
    }

    async onRefresh() {
        await this._loadDashboardData();
        this.notification.add("Dashboard refreshed", { type: "info" });
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    getStatusBadgeClass(state) {
        return {
            draft: "ff-badge-draft",
            dispatched: "ff-badge-dispatched",
            completed: "ff-badge-completed",
            cancelled: "ff-badge-cancelled",
        }[state] || "ff-badge-draft";
    }

    getStatusLabel(state) {
        return {
            draft: "Draft",
            dispatched: "On Trip",
            completed: "Completed",
            cancelled: "Cancelled",
        }[state] || state;
    }

    formatDate(dt) {
        if (!dt) return "—";
        const d = new Date(dt);
        return d.toLocaleString("en-IN", {
            day: "2-digit", month: "short", year: "numeric",
            hour: "2-digit", minute: "2-digit",
        });
    }

    getSortIcon(field) {
        if (this.state.sortField !== field) return "↕";
        return this.state.sortAsc ? "↑" : "↓";
    }
}

registry.category("actions").add("fleetflow_dashboard", FleetFlowDashboard);
