/** @odoo-module **/

import {useService} from "@web/core/utils/hooks";
import {_t} from "@web/core/l10n/translation";
import {VariableFormDialog} from "@sot_mrp_formula_builder/components/formula_variable/variable_form_dialog";

import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {Component, onWillStart, useState,} from "@odoo/owl";
import {registry} from "@web/core/registry";

export class FormulaBuilder extends Component {
    static props = {
        ...standardFieldProps,
        business_domain: {type: String, optional: true},
        account_field: {type: String, optional: true},
        product_field: {type: String, optional: true},
        amount_field: {type: String, optional: true},
        business_domain_compute: {type: String, optional: true},
        force_applicability: {type: String, optional: true},
        allow_save: {type: Boolean, optional: true},
    }

    setup() {
        this.actionService = useService("action");
        this.orm = useService("orm");
        this.dialogService = useService("dialog");
        // this.components = extractLayoutComponents(this.env.config);

        this.state = useState({
            showDropdown: false,
            formattedData: [],
            numbers: [],
            operations: [],
            functions: [],
            variables: [],
            outputFormula: "",
            formulaName: "",
            variableName: "",
        });

        onWillStart(this.willStart);
        // useRecordObserver(this.willUpdateRecord.bind(this));
        // onPatched(this.patched);

        // useExternalListener(window, "click", this.onWindowClick, true);
        // useExternalListener(window, "resize", this.onWindowResized);
    }

    // Lifecycle
    async willStart() {
        if (this.editingRecord) {
            // for performance in list views, plans are not retrieved until they are required.
            // await this.fetchAllPlans();

        }
        this.setMathValues();
        // await this.jsonToData();
    }

    async willUpdateRecord(record) {
        // Unless force_applicability, Plans need to be retrieved again as the product or account might have changed
        // and thus different applicabilities apply
        // or a model applies that contains unavailable plans
        // This should only execute when these fields have changed, therefore we use the `_field` props.
        // const valueChanged =
        //     JSON.stringify(this.currentValue) !==
        //     JSON.stringify(record.data[this.props.name]);
        // const currentAccount = this.props.account_field && record.data[this.props.account_field] || false;
        // const currentProduct = this.props.product_field && record.data[this.props.product_field] || false;
        // const accountChanged = !shallowEqual(this.lastAccount, currentAccount);
        // const productChanged = !shallowEqual(this.lastProduct, currentProduct);
        // if (valueChanged || accountChanged || productChanged) {
        //     // if (!this.props.force_applicability) {
        //     //     await this.fetchAllPlans();
        //     // }
        //     // this.lastAccount = accountChanged && currentAccount || this.lastAccount;
        //     // this.lastProduct = productChanged && currentProduct || this.lastProduct;
        //     // await this.jsonToData();
        // }
        // this.currentValue = record.data[this.props.name];
    }

    patched() {
        this.focusToSelector();
    }

    // Methods
    setMathValues() {
        this.state.numbers = [
            {id: 1, value: 1},
            {id: 2, value: 2},
            {id: 3, value: 3},
            {id: 4, value: '+'},
            {id: 5, value: 4},
            {id: 6, value: 5},
            {id: 7, value: 6},
            {id: 8, value: '-'},
            {id: 9, value: 7},
            {id: 10, value: 8},
            {id: 11, value: 9},
            {id: 12, value: '*'},
            {id: 13, value: 0},
            {id: 14, value: '.'},
            {id: 15, value: '%'},
            {id: 16, value: '/'},
        ];

        this.state.operations = [
            {id: 1, value: '('},
            {id: 2, value: ')'},
            {id: 3, value: '['},
            {id: 4, value: ']'},
        ];

        this.state.functions = [
            {id: 1, value: 'SUM'},
            {id: 2, value: 'AVG'},
            {id: 3, value: 'MIN'},
            {id: 4, value: 'MAX'},
            {id: 5, value: 'COUNT'},
            {id: 6, value: 'CEIL'},
            {id: 7, value: 'FLOOR'},
            {id: 8, value: 'ROUND'},
        ];
    }

    setFormula(ev, value) {
        const formula = this.state.outputFormula;
        this.state.outputFormula = formula + value;
    }

    clearFormulaText(ev) {
        this.state.outputFormula = "";
    }

    delFormulaText(ev) {
        const formula = this.state.outputFormula;
        if (formula.length > 0) {
            this.state.outputFormula = formula.slice(0, -1);
        }
    }

    openVariableFormDialog(ev) {
        const dialogProps = {
            title: _t("Please Select Purchase By before submit"),
            body: {
                'formulaName': "Create new variable",
            },
            confirm: async (value) => {
                const id = this.state.variables.length + 1;
                this.state.variables.push({id: id, value: value.name});
            },
            cancel: () => {
                console.log("cancel")
            },
        };

        this.dialogService.add(VariableFormDialog, dialogProps);
    }

    async saveFormula(ev) {
        await this.orm.create("formula.formula", [{
            name: this.state.formulaName,
            description: this.state.formulaName,
            formula: this.state.outputFormula,
            variables: {"variables": this.state.variables.map(v => v.value)},
        }]);
    }

    onFormulaNameChange(ev) {
        this.state.formulaName = ev.target.value;
    }

    onVariableNameChange(ev) {
        this.state.variableName = ev.target.value;
    }
}

FormulaBuilder.template = "sot_mrp_formula_builder.FormulaBuilder";
registry.category("actions").add("formula_builder", FormulaBuilder);