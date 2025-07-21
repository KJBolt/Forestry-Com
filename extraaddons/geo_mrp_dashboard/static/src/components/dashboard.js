/** @odoo-module */

import { registry } from "@web/core/registry";
// import { KpiCardDraft, CrossCutDraft, HaulingDraft, LogInformationDraft, KpiCardApproved, CrossCutApproved, HaulingApproved, LogInformationApproved } from "./kpi_card/kpi_card";
import { MrpChartRenderer } from "./chart_renderer/chart_renderer";
import { useService } from "@web/core/utils/hooks";

const { Component, onWillStart, useState } = owl;

export class MrpDashboard extends Component {
    setup() {
        this.state = useState({
            draft: {},
            approved: {},
            period: '1',
            fromDate: '',
            toDate: '',
            date: moment().format('YYYY-MM-DD HH:mm:ss'), // default date
            selectedForestReverseId: null,
            CollectionChart: {
                data: {
                    labels: [],
                    datasets: []
                }
            },
            forestReverseOptions: []
        });

        this.orm = useService("orm");
        this.actionService = useService("action");
        this.userService = useService("user");
        onWillStart(async () => {
            await this.initializeDashboard();
        });
    }

    async initializeDashboard() {
        await this.loadForestReverseOptions();
        await this.updateDashboardData();
    }

    async loadForestReverseOptions() {
        const options = await this.orm.searchRead("mrp.production", [], ['name']);
        this.state.forestReverseOptions = options.map(option => ({ id: option.id, name: option.name }));
    }

    async updateDashboardData() {
        await this.getDates();
    
        const states = ['draft', 'approved', 'confirmed', 'pendingWithOthers'];
        const models = ['mrp.production.batch', 'mrp.production'];
    
        const fetchPromises = [];
    
        for (const state of states) {
            for (const model of models) {
                fetchPromises.push(this.fetchDataForState(state, model, state === 'pendingWithOthers' ? [] : [state]));
            }
        }
    
        fetchPromises.push(this.getCollectionChart());
        fetchPromises.push(this.ProductChart());
    
        await Promise.all(fetchPromises);
    }
    
    async fetchDataForState(stateKey, model, states) {
        let domain = [
            ['state', 'in', states],
        ];
    
        if (stateKey === 'pendingWithOthers') {
            // Set the domain to filter out records created by the current user
            const currentUserId = this.userService.uid;
            domain = [
                ['state', '=', 'draft'],
                ['create_uid', '!=', currentUserId]
            ];
        }
    
        const count = await this.orm.searchCount(model, domain);
        
        if (!this.state[stateKey]) {
            this.state[stateKey] = {};  
        }
        
        this.state[stateKey][model] = count;  
    }

    async getCollectionChart() {
        // Use stock.quant model to group data by warehouse_id
        const data = await this.orm.readGroup("stock.quant", [], ['location_id'], ['location_id']);
        
        const total = data.reduce((acc, curr) => acc + curr.location_id_count, 0);
        
        const backgroundColors = ['#36a2eb', '#ffcd56', '#ff6384', '#4bc0c0', '#9966ff'];
    
        this.state.CollectionChart = {
            data: {
                labels: data.map(d => d.location_id ? d.location_id[1] : 'Unknown'),
                datasets: [{
                    label: 'Total',
                    data: data.map(d => (d.location_id_count / total) * 100),
                    backgroundColor: backgroundColors.slice(0, data.length),
                    hoverOffset: 4,
                }]
            }
        };
    }

    async ProductChart() {
        const domain = [['state', '=', 'confirmed']]; // Adjust the domain as per your criteria
        const data = await this.orm.readGroup("mrp.production", domain, ['product_id'], ['product_id']);
        const total = data.reduce((acc, curr) => acc + curr.product_id_count, 0);
    
        // Generate random colors for each dataset
        const backgroundColors = this.generateRandomColors(data.length);
    
        this.state.ProductChart = {
            data: {
                labels: data.map(d => d.product_id ? d.product_id[1] : 'Unknown'),
                datasets: [{
                    label: 'Product Production',
                    data: data.map(d => (d.product_id_count / total) * 100),
                    backgroundColor: backgroundColors,
                    hoverOffset: 4,
                }]
            }
        };
    }
    
    generateRandomColors(numColors) {
        // Function to generate random colors
        const colors = [];
        for (let i = 0; i < numColors; i++) {
            const color = `rgba(${Math.floor(Math.random() * 256)}, ${Math.floor(Math.random() * 256)}, ${Math.floor(Math.random() * 256)}, 0.8)`;
            colors.push(color);
        }
        return colors;
    }

    onPeriodChange(ev) {
        this.state.period = ev.target.value;
        this.onChangePeriod();
    }

    onFromDateChange(ev) {
        this.state.fromDate = ev.target.value;
        if (this.state.period === 'custom') {
            this.onChangePeriod();
        }
    }

    onToDateChange(ev) {
        this.state.toDate = ev.target.value;
        if (this.state.period === 'custom') {
            this.onChangePeriod();
        }
    }

    async onCustomDateSelect() {
        this.state.period = 'custom';
        this.state.fromDate = document.getElementById('fromDate').value;
        this.state.toDate = document.getElementById('toDate').value;
        await this.onChangePeriod();
    }

    async onChangePeriod() {
        await this.updateDashboardData();
    }

    getDates() {
        if (this.state.period === 'custom' && this.state.fromDate && this.state.toDate) {
            this.state.date = moment(this.state.fromDate, 'YYYY-MM-DD').format('YYYY-MM-DD HH:mm:ss');
        } else {
            this.state.date = moment().subtract(this.state.period, 'days').format('YYYY-MM-DD HH:mm:ss');
        }
    }

    async viewRecords(state, model, viewName) {
        const domain = [
            ['state', 'in', [state]],
            // ['create_date', '>', this.state.date]
        ];
        const list_view = await this.orm.searchRead("ir.model.data", [['name', '=', viewName]], ['res_id']);
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: state.charAt(0).toUpperCase() + state.slice(1),
            res_model: model,
            domain,
            views: [
                [list_view.length > 0 ? list_view[0].res_id : false, "list"],
                [false, "form"],
            ]
        });
    }

    // async ViewDraft() {
    //     await this.viewRecords('draft', 'mrp.bom', 'mrp_bom_tree_view');
    // }

    // async ViewApproved() {
    //     await this.viewRecords('approved', 'mrp.bom', 'mrp_bom_tree_view');
    // }

    async MopViewDraft() {
        await this.viewRecords('draft', 'mrp.production', 'mrp_production_tree_view');
    }

    async MopViewConfirmed() {
        await this.viewRecords('confirmed', 'mrp.production', 'mrp_production_tree_view');
    }

    async MobViewDraft() {
        await this.viewRecords('draft', 'mrp.production.batch', 'mrp_production_batch_tree');
    }

    async MopViewApproved() {
        await this.viewRecords('approved', 'mrp.production.batch', 'mrp_production_batch_tree');
    }


    async fetchPendingWithOthersDomain() {
        const currentUserId = this.userService.uid;
        return [
            ['state', '=', 'draft'],
            ['create_uid', '!=', currentUserId] // Exclude records created by the current user
        ];
    }
    
    // async viewPendingWithOthersBom() {
    //     const customDomain = await this.fetchPendingWithOthersDomain();
    //     await this.viewRecords('draft', 'mrp.bom', 'mrp_bom_tree_view', customDomain);
    // }
    
    async viewPendingWithOthersMrpOrder() {
        const customDomain = await this.fetchPendingWithOthersDomain();
        await this.viewRecords('draft', 'mrp.production', 'mrp_production_tree_view', customDomain);
    }
    
    async viewPendingWithOthersOperationMrp() {
        const customDomain = await this.fetchPendingWithOthersDomain();
        await this.viewRecords('draft', 'mrp.production.batch', 'mrp_production_batch_tree', customDomain);
    }
    
}

MrpDashboard.template = "Mrp.Dashboard";
MrpDashboard.components = {
    // KpiCardDraft,
    // CrossCutDraft,
    // HaulingDraft,
    // LogInformationDraft,

    // KpiCardApproved,
    // CrossCutApproved,
    // HaulingApproved,
    // LogInformationApproved,

    MrpChartRenderer
};

registry.category("actions").add("MrpDashboard", MrpDashboard);
