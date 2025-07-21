/** @odoo-module **/

import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {getNextTabableElement, getPreviousTabableElement} from "@web/core/utils/ui";
import {usePosition} from "@web/core/position_hook";
import {_t} from "@web/core/l10n/translation";

import {standardFieldProps} from "@web/views/fields/standard_field_props";

import {Component, onPatched, useExternalListener, useRef, useState, onWillStart} from "@odoo/owl";
import {useRecordObserver} from "@web/model/relational_model/utils";

export class FormulaCalculator extends Component {
    static template = "sot_mrp_formula_builder.FormulaCalculator";

    static props = {
        ...standardFieldProps,
        formula_variable_field: {type: String, optional: false},
        formula_text_field: {type: String, optional: false},
        formula_field: {type: String, optional: false},
        formula_value_field: {type: String, optional: false},
    }

    setup() {
        this.orm = useService("orm");

        this.state = useState({
            showDropdown: false,
            formattedResult: this.props.record.data[this.props.name] || 0,
            formattedData: [],
        });

        this.widgetRef = useRef("formulaValueCalculator");
        this.dropdownRef = useRef("formulaValueDropdown");
        this.mainRef = useRef("mainElement");
        this.addLineButton = useRef("addLineButton");
        usePosition("formulaValueDropdown", () => this.widgetRef.el);

        this.focusSelector = false;
        this.setDefaultValues();

        onWillStart(this.willStart);

        useRecordObserver(this.willUpdateRecord.bind(this));
        onPatched(this.patched);
        useExternalListener(window, "click", this.onWindowClick, true);
        useExternalListener(window, "resize", this.onWindowResized);
    }

    // Lifecycle
    async willStart() {
        if (this.editingRecord) {
            // for performance in list views, plans are not retrieved until they are required.
            await this.fetchAllVariables();
        }
    }

    async willUpdateRecord(record) {
        // Unless force_applicability, Plans need to be retrieved again as the product or account might have changed
        // and thus different applicabilities apply
        // or a model applies that contains unavailable plans
        // This should only execute when these fields have changed, therefore we use the `_field` props.
        console.log("this.props.record.data", this.props.record.data);
        console.log("record", record);
        await this.fetchAllVariables();
        this.setDefaultValues();
    }

    patched() {
        this.focusToSelector();
    }

    get editingRecord() {
        return !this.props.readonly;
    }

    get isDropdownOpen() {
        return this.state.showDropdown && !!this.dropdownRef.el;
    }

    async fetchAllVariables() {
        this.allAvailableVariables = await this.orm.call("formula.variable", "get_all_formula_variable_dict", [""], {});
    }

    setDefaultValues() {
        this.allVariables = [];
        if (this.props.record.data[this.props.formula_variable_field]) {
            this.allVariables = this.props.record.data[this.props.formula_variable_field].variables || {};
        }
        console.log("this.props.formula_variable_field", this.props.formula_variable_field);
        console.log("this.props.record.data[this.props.formula_variable_field]", this.props.record.data[this.props.formula_variable_field]);
        console.log("this.props.record.data[this.props.formula_value_field]", this.props.record.data[this.props.formula_value_field]);
        this.allVariableValues = this.props.record.data[this.props.formula_value_field] || {};
        this.formulaText = this.props.record.data[this.props.formula_text_field] || "";
        this.formattedResult = this.props.record.data[this.props.name];
    }

    reload() {
        this.setDefaultValues();
        this.closeFormulaValueEditor();
        this.openFormulaEditor();
    }

    onVariableValueChange(ev) {
        this.allVariableValues[ev.target.id] = Number(ev.target.value);
    }

    async onCalculateFormula(ev) {
        this.closeFormulaValueEditor();
        this.save();
    }

    async evalFormula() {
        return await this.orm.call('formula.formula', "compute_formula", ["", this.formulaText, this.allVariableValues], {});
    }

    save() {
        const self = this;
        self.preventOpen = true;

        try {
            self.evalFormula().then((res) => {
                self.state.formattedResult = res;

                const variableVals = self.allVariableValues;
                // convert all values to number
                for (const [key, value] of Object.entries(variableVals)) {
                    variableVals[key] = Number(value);
                }

                self.props.record.update({[self.props.formula_value_field]: variableVals});
                self.props.record.update({[self.props.name]: self.state.formattedResult});

                self.preventOpen = false;
            });
        } catch (e) {
            self.preventOpen = false;
        } finally {
            self.preventOpen = false;
        }
    }

    forceCloseEditor() {
        // focus to the main Element but the dropdown should not open
        this.preventOpen = true;
        this.closeFormulaValueEditor();
        this.mainRef.el.focus();
        this.preventOpen = false;
    }

    closeFormulaValueEditor() {
        this.state.showDropdown = false;
    }

    openFormulaEditor() {
        this.setFocusSelector("[name='line_0'] td:first-of-type");
        this.state.showDropdown = true;
    }

    // Focus
    onFormulaElementFocus(ev) {
        if (!this.isDropdownOpen && !this.preventOpen) {
            this.openFormulaEditor();
        }
    }

    focusToSelector() {
        if (this.focusSelector && this.isDropdownOpen) {
            this.focus(this.adjacentElementToFocus("next", this.dropdownRef.el.querySelector(this.focusSelector)));
        }
        this.focusSelector = false;
    }

    setFocusSelector(selector) {
        this.focusSelector = selector;
    }

    adjacentElementToFocus(direction, el = null) {
        if (!this.isDropdownOpen) {
            return null;
        }
        if (!el) {
            el = this.dropdownRef.el;
        }
        return direction === "next" ? getNextTabableElement(el) : getPreviousTabableElement(el);
    }

    focusAdjacent(direction) {
        const elementToFocus = this.adjacentElementToFocus(direction);
        if (elementToFocus) {
            this.focus(elementToFocus);
            return true;
        }
        return false;
    }

    focus(el) {
        if (!el) return;
        el.focus();
        if (["INPUT", "TEXTAREA"].includes(el.tagName)) {
            if (el.selectionStart) {
                el.selectionStart = 0;
                el.selectionEnd = el.value.length;
            }
            el.select();
        }
    }

    onWindowClick(ev) {
        //TODO: dragging the search more dialog should not close the popup either
        const modal = document.querySelector(".modal");
        const clickedInSearchMoreDialog = modal && modal.querySelector('.o_list_view') && modal.contains(ev.target);
        if (this.isDropdownOpen
            && !this.widgetRef.el.contains(ev.target)
            && !clickedInSearchMoreDialog
        ) {
            this.forceCloseEditor();
        }
    }

    onWindowResized() {
        // popup ui is ugly when window is resized, so close it
        if (this.isDropdownOpen) {
            this.forceCloseEditor();
        }
    }
}

export const formulaValueCalculator = {
    component: FormulaCalculator,
    supportedTypes: ["char", "text"],
    fieldDependencies: [{name: "formula_id", type: "number"}, {name: 'formula_text', type: "text"}],
    supportedOptions: [
        {
            label: _t("Formula Variables"),
            name: "formula_variable_field",
            type: "string",
        },
        {
            label: _t("Formula Values"),
            name: "formula_value_field",
            type: "string",
        },
        {
            label: _t("Formula Text"),
            name: "formula_text_field",
            type: "string",
        },
        {
            label: _t("Formula field"),
            name: "formula_field",
            type: "field",
            availableTypes: ["many2one"],
        },
    ],
    extractProps: ({attrs, options}) => ({
        formula_variable_field: options.formula_variable_field,
        formula_value_field: options.formula_value_field,
        formula_text_field: options.formula_text_field,
        formula_field: options.formula_field,
    }),
};

registry.category("fields").add("formula_value_calculator", formulaValueCalculator);
