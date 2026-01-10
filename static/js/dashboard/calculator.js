// ============================================================================
// RATE CALCULATOR FUNCTIONALITY
// ============================================================================

// Toggle Tab
function switchCalculatorTab(tab) {
    document.querySelectorAll('.calc-tab-btn').forEach(btn => {
        btn.classList.remove('bg-brand-blue', 'text-white');
        btn.classList.add('text-slate-600');
        if (btn.dataset.tab === tab) {
            btn.classList.remove('text-slate-600');
            btn.classList.add('bg-brand-blue', 'text-white');
        }
    });

    document.querySelectorAll('.calc-tab-content').forEach(content => content.classList.add('hidden'));
    document.getElementById(`calc-${tab}-tab`).classList.remove('hidden');
}

// ============================================================================
// GLOBAL STATE & CONSTANTS
// ============================================================================

// State for Calculator Boxes
// Initial state: one box with default dimensions and order value
let calculatorBoxes = [
    { id: 1, weight: '', length: 10, width: 10, height: 10, orderValue: '' }
];

// Global dimension unit (applies to all boxes)
let globalDimensionUnit = 'cm';

// Volumetric Divisor (Mirroring Backend)
// TODO: Ideally fetch this from an API endpoint on load
const VOLUMETRIC_DIVISOR = 5000;

// ============================================================================
// UNIT CONVERSION HELPERS
// ============================================================================

// Convert dimension from any unit to centimeters
function convertToCm(value, unit) {
    const conversions = {
        'cm': 1,
        'mm': 0.1,
        'm': 100,
        'in': 2.54,
        'ft': 30.48
    };
    return value * (conversions[unit] || 1);
}

// Update global dimension unit for all boxes
function updateGlobalDimensionUnit(unit) {
    globalDimensionUnit = unit;
    calculateBoxTotals(); // Recalculate with new unit
}

// ============================================================================
// HELPER FUNCTIONS (Global Scope for HTML access)
// ============================================================================

// Initialize Calculator
function initCalculator() {
    console.log("Calculator Initializing...");

    // Render immediately if container exists (fix for initial load)
    if (document.getElementById('calc-box-list')) {
        console.log("Found box list container, rendering...");
        renderCalculatorBoxes();
    }

    // Hook into showSection navigation
    const originalShowSection = window.showSection;
    if (originalShowSection) {
        window.showSection = function (section) {
            originalShowSection(section);
            if (section === 'rate-calculator') {
                document.getElementById('page-title').textContent = 'Rate Calculator';
                document.getElementById('header-actions').innerHTML = '';

                // Fetch Divisor from backend if possible, else use default
                const volDisplay = document.getElementById('vol-divisor-display');
                if (volDisplay) volDisplay.textContent = VOLUMETRIC_DIVISOR;

                // Render initial boxes if not already done
                renderCalculatorBoxes();

                // Init FTL dropdowns if data ready
                if (window.ftlRatesData && Object.keys(ftlRatesData).length > 0) {
                    initFTLCalcDropdowns();
                } else if (window.loadFTLRatesData) {
                    loadFTLRatesData().then(initFTLCalcDropdowns);
                }
            }
        };
    }
}

// Render Box List
function renderCalculatorBoxes() {
    const container = document.getElementById('calc-box-list');
    if (!container) return;

    container.innerHTML = calculatorBoxes.map((box, index) => `
    <div class="relative grid grid-cols-2 md:grid-cols-5 gap-3 p-3 bg-white border border-slate-200 rounded-lg group">
        ${calculatorBoxes.length > 1 ? `
            <button type="button" onclick="removeCalculatorBox(${box.id})" 
                class="absolute -top-2 -right-2 bg-red-100 text-red-600 rounded-full w-5 h-5 flex items-center justify-center hover:bg-red-200 transition-colors shadow-sm">
                &times;
            </button>
        ` : ''}
        
        <div>
            <label class="block text-[10px] uppercase font-bold text-slate-400 mb-1 h-6 flex items-center">Weight (kg)</label>
            <input type="number" step="0.01" min="0.01" value="${box.weight}" 
                id="calc-weight-${box.id}"
                class="w-full px-2 py-1.5 text-sm border border-slate-300 rounded focus:ring-1 focus:ring-brand-blue"
                onchange="updateCalculatorBox(${box.id}, 'weight', this.value)" 
                onblur="validateCalcField(this, 'weight')"
                oninput="clearCalcError(this)"
                placeholder="0.00">
        </div>
        <div>
            <label class="block text-[10px] uppercase font-bold text-slate-400 mb-1 h-6 flex items-center">Length</label>
            <input type="number" step="0.1" min="0.1" value="${box.length}" 
                id="calc-length-${box.id}"
                class="w-full px-2 py-1.5 text-sm border border-slate-300 rounded focus:ring-1 focus:ring-brand-blue"
                onchange="updateCalculatorBox(${box.id}, 'length', this.value)" 
                onblur="validateCalcField(this, 'dimension')"
                oninput="clearCalcError(this)"
                placeholder="10">
        </div>
        <div>
            <label class="block text-[10px] uppercase font-bold text-slate-400 mb-1 h-6 flex items-center">Width</label>
            <input type="number" step="0.1" min="0.1" value="${box.width}" 
                id="calc-width-${box.id}"
                class="w-full px-2 py-1.5 text-sm border border-slate-300 rounded focus:ring-1 focus:ring-brand-blue"
                onchange="updateCalculatorBox(${box.id}, 'width', this.value)" 
                onblur="validateCalcField(this, 'dimension')"
                oninput="clearCalcError(this)"
                placeholder="10">
        </div>
        <div>
            <label class="block text-[10px] uppercase font-bold text-slate-400 mb-1 h-6 flex items-center">Height</label>
            <input type="number" step="0.1" min="0.1" value="${box.height}" 
                id="calc-height-${box.id}"
                class="w-full px-2 py-1.5 text-sm border border-slate-300 rounded focus:ring-1 focus:ring-brand-blue"
                onchange="updateCalculatorBox(${box.id}, 'height', this.value)" 
                onblur="validateCalcField(this, 'dimension')"
                oninput="clearCalcError(this)"
                placeholder="10">
        </div>
        <div>
            <label class="block text-[10px] uppercase font-bold text-slate-400 mb-1 h-6 flex items-center">Value (₹) <span class="text-slate-300 font-normal">(optional)</span></label>
            <input type="number" step="0.01" min="0" value="${box.orderValue}" 
                id="calc-value-${box.id}"
                class="w-full px-2 py-1.5 text-sm border border-slate-300 rounded focus:ring-1 focus:ring-brand-blue"
                onchange="updateCalculatorBox(${box.id}, 'orderValue', this.value)" 
                onblur="validateCalcField(this, 'value')"
                oninput="clearCalcError(this)"
                placeholder="0">
        </div>
    </div>
    `).join('');

    calculateBoxTotals();
}

// Add a new box
function addCalculatorBox() {
    const newId = Math.max(...calculatorBoxes.map(b => b.id), 0) + 1;
    calculatorBoxes.push({ id: newId, weight: '', length: 10, width: 10, height: 10, orderValue: '' });
    renderCalculatorBoxes();
}

// Remove a box
function removeCalculatorBox(id) {
    if (calculatorBoxes.length <= 1) return;
    calculatorBoxes = calculatorBoxes.filter(b => b.id !== id);
    renderCalculatorBoxes();
}

// Update box field
function updateCalculatorBox(id, field, value) {
    const box = calculatorBoxes.find(b => b.id === id);
    if (box) {
        box[field] = field === 'orderValue' ? (parseFloat(value) || 0) : (parseFloat(value) || 0);

        // Handle specialized formatting if needed, but for now generic parsing works
        if (field === 'weight' && box[field] < 0) box[field] = 0;

        calculateBoxTotals();
    }
}

// Calculate totals
function calculateBoxTotals() {
    let totalActual = 0;
    let totalApplicable = 0;
    let totalOrderValue = 0;

    calculatorBoxes.forEach(box => {
        const w = parseFloat(box.weight) || 0;
        // Convert dimensions to cm before calculating using global unit
        const l = convertToCm(parseFloat(box.length) || 0, globalDimensionUnit);
        const wid = convertToCm(parseFloat(box.width) || 0, globalDimensionUnit);
        const h = convertToCm(parseFloat(box.height) || 0, globalDimensionUnit);
        const val = parseFloat(box.orderValue) || 0;

        const vol = (l * wid * h) / VOLUMETRIC_DIVISOR;
        const appl = Math.max(w, vol);

        totalActual += w;
        totalApplicable += appl;
        totalOrderValue += val;
    });

    const totalActualEl = document.getElementById('total-actual-weight');
    const totalApplicableEl = document.getElementById('total-applicable-weight');
    const totalOrderValueEl = document.getElementById('total-order-value');

    if (totalActualEl) totalActualEl.textContent = totalActual.toFixed(2) + ' kg';
    if (totalApplicableEl) totalApplicableEl.textContent = totalApplicable.toFixed(2) + ' kg';
    if (totalOrderValueEl) totalOrderValueEl.value = totalOrderValue.toFixed(2);

    return { totalApplicable, totalOrderValue };
}

// ============================================================================
// VALIDATION FUNCTIONS FOR CALCULATOR
// ============================================================================

// Validate calculator field based on type
function validateCalcField(input, type) {
    const value = parseFloat(input.value);
    let isValid = true;
    let errorMessage = '';

    switch (type) {
        case 'weight':
            // Weight must be positive
            isValid = !isNaN(value) && value > 0;
            if (!isValid) {
                errorMessage = input.value === '' ? 'Weight is required' : 'Weight must be greater than 0';
            }
            break;
        case 'dimension':
            // Dimensions must be positive
            isValid = !isNaN(value) && value > 0;
            if (!isValid) {
                errorMessage = input.value === '' ? 'Dimension is required' : 'Dimension must be greater than 0';
            }
            break;
        case 'value':
            // Value is optional but must be non-negative if provided
            isValid = input.value === '' || (!isNaN(value) && value >= 0);
            if (!isValid) {
                errorMessage = 'Value must be 0 or greater';
            }
            break;
        case 'pincode':
            // Pincode must be exactly 6 digits
            isValid = /^\d{6}$/.test(input.value);
            if (!isValid) {
                if (input.value === '') {
                    errorMessage = 'Pincode is required';
                } else if (input.value.length < 6) {
                    errorMessage = 'Pincode must be 6 digits';
                } else {
                    errorMessage = 'Invalid pincode format';
                }
            }
            break;
    }

    // Remove existing error message
    const existingError = input.parentElement.querySelector('.validation-error');
    if (existingError) {
        existingError.remove();
    }

    if (!isValid) {
        input.classList.remove('border-slate-300');
        input.classList.add('border-red-500', 'border-2');

        // Add error message below the field
        const errorDiv = document.createElement('div');
        errorDiv.className = 'validation-error text-red-600 text-xs mt-1';
        errorDiv.textContent = errorMessage;
        input.parentElement.appendChild(errorDiv);
    } else {
        input.classList.remove('border-red-500', 'border-2');
        input.classList.add('border-slate-300');
    }

    return isValid;
}

// Clear error styling from calculator field
function clearCalcError(input) {
    input.classList.remove('border-red-500', 'border-2');
    input.classList.add('border-slate-300');

    // Remove error message if exists
    const existingError = input.parentElement.querySelector('.validation-error');
    if (existingError) {
        existingError.remove();
    }
}

// Calculate Regular Rate AND Send to API
async function calculateRegularRate(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);

    const source = formData.get('source_pincode');
    const dest = formData.get('dest_pincode');

    // Validate pincodes first
    const sourcePincodeInput = form.querySelector('input[name="source_pincode"]');
    const destPincodeInput = form.querySelector('input[name="dest_pincode"]');

    let isValid = true;

    if (!validateCalcField(sourcePincodeInput, 'pincode')) {
        isValid = false;
    }

    if (!validateCalcField(destPincodeInput, 'pincode')) {
        isValid = false;
    }

    // Validate all box fields
    calculatorBoxes.forEach(box => {
        const weightInput = document.getElementById(`calc-weight-${box.id}`);
        const lengthInput = document.getElementById(`calc-length-${box.id}`);
        const widthInput = document.getElementById(`calc-width-${box.id}`);
        const heightInput = document.getElementById(`calc-height-${box.id}`);
        const valueInput = document.getElementById(`calc-value-${box.id}`);

        if (weightInput && !validateCalcField(weightInput, 'weight')) {
            isValid = false;
        }
        if (lengthInput && !validateCalcField(lengthInput, 'dimension')) {
            isValid = false;
        }
        if (widthInput && !validateCalcField(widthInput, 'dimension')) {
            isValid = false;
        }
        if (heightInput && !validateCalcField(heightInput, 'dimension')) {
            isValid = false;
        }
        if (valueInput && !validateCalcField(valueInput, 'value')) {
            isValid = false;
        }
    });

    // If validation failed, stop here
    if (!isValid) {
        if (window.toast) {
            toast.error("Please fix the validation errors before calculating rates");
        }
        return;
    }

    // Validate Boxes
    const validBoxes = calculatorBoxes.filter(b => b.weight > 0);
    if (validBoxes.length === 0) {
        toast.error("Please add at least one box with valid weight");
        return;
    }

    const isCod = formData.get('is_cod') === 'true';
    const totals = calculateBoxTotals();
    const orderValue = totals.totalOrderValue;

    const resultsList = document.getElementById('calc-regular-list');
    const resultsContainer = document.getElementById('calc-regular-results');

    try {
        if (typeof showLoading === 'function') {
            showLoading('calc-regular-list', 'Fetching best rates...');
        } else {
            resultsList.innerHTML = '<div class="text-center py-6 text-slate-500">Fetching best rates...</div>';
        }

        resultsContainer.classList.remove('hidden');

        const requestData = {
            source_pincode: parseInt(source),
            dest_pincode: parseInt(dest),
            is_cod: isCod,
            order_value: orderValue,
            mode: 'Both',
            // Send orders list with dimensions converted to cm using global unit
            orders: validBoxes.map(b => {
                return {
                    weight: parseFloat(b.weight),
                    length: convertToCm(parseFloat(b.length), globalDimensionUnit),
                    width: convertToCm(parseFloat(b.width), globalDimensionUnit),
                    height: convertToCm(parseFloat(b.height), globalDimensionUnit)
                };
            })
        };

        const response = await fetch(`${API_BASE}/api/compare-rates`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });

        if (response.ok) {
            const rates = await response.json();
            renderRegularRates(rates);
        } else {
            const error = await response.json();
            let errorMsg = error.detail || 'Failed to fetch rates';

            // Log specific error codes if available
            console.warn(`Rate Calculation Failed: ${response.status}`, error);

            // Show toast for user awareness
            if (window.toast) toast.error(errorMsg);

            // Show error in the list area
            resultsList.innerHTML = `
                <div class="text-center py-6 text-red-600 bg-red-50 rounded-lg border border-red-100 p-4">
                    <p class="font-semibold mb-1">Calculation Failed</p>
                    <p class="text-sm">${errorMsg}</p>
                    <button onclick="document.getElementById('regular-calc-form').requestSubmit()" class="mt-3 px-4 py-1.5 bg-white border border-red-200 text-red-600 text-xs rounded hover:bg-red-50 transition-colors">
                        Try Again
                    </button>
                </div>
            `;
        }
    } catch (error) {
        console.error('Rate calc error:', error);

        const isNetworkError = error.name === 'TypeError' && error.message === 'Failed to fetch';
        const msg = isNetworkError ? "Network Error: Unable to connect to server" : "An unexpected error occurred";

        if (window.toast) toast.error(msg);

        resultsList.innerHTML = `
            <div class="text-center py-6 text-red-600 bg-red-50 rounded-lg border border-red-100 p-4">
                <p class="font-semibold mb-1">Connection Error</p>
                <p class="text-sm">Unable to connect to the pricing engine.</p>
                <p class="text-xs mt-1 text-slate-500">Please check your internet connection and try again.</p>
                <button onclick="document.getElementById('regular-calc-form').requestSubmit()" class="mt-3 px-4 py-1.5 bg-white border border-red-200 text-red-600 text-xs rounded hover:bg-red-50 transition-colors">
                    Retry Connection
                </button>
            </div>
        `;
    }
}

function renderRegularRates(rates) {
    const container = document.getElementById('calc-regular-list');
    if (rates.length === 0) {
        container.innerHTML = '<div class="text-center py-4 text-slate-500">No carriers available for this route.</div>';
        return;
    }

    const html = rates.map((rate, index) => {
        const breakdown = rate.breakdown || {};
        const breakdownId = `breakdown-${index}`;

        // Helper to create breakdown row only if value exists and is non-zero
        const createRow = (label, value) => {
            if (!value || value === 0) return '';
            return `
                <div class="flex justify-between items-center">
                    <span class="text-slate-600">${label}:</span>
                    <span class="font-semibold text-slate-800">₹${value.toFixed(2)}</span>
                </div>`;
        };

        const formattedZone = (rate.zone || "").replace(/\b[a-z]/g, char => char.toUpperCase());

        return `
    <div class="bg-white border border-slate-200 rounded-lg overflow-hidden hover:border-brand-blue transition-all">
        <div class="p-4 flex items-center justify-between cursor-pointer" onclick="toggleBreakdown('${breakdownId}')">
            <div class="flex items-center space-x-4">
                <div class="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-600 font-bold">
                    ${rate.carrier.charAt(0)}
                </div>
                <div>
                    <h4 class="font-semibold text-slate-800">${rate.carrier}</h4>
                    <div class="text-xs text-slate-500">${rate.mode} • ${formattedZone}</div>
                </div>
            </div>
            <div class="flex items-center space-x-3">
                <div class="text-right">
                    <div class="font-bold text-lg text-brand-blue">₹${rate.total_cost.toFixed(2)}</div>
                    <div class="text-xs text-slate-500">Click for breakdown</div>
                </div>
                <svg class="w-5 h-5 text-slate-400 transition-transform duration-200" id="${breakdownId}-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                </svg>
            </div>
        </div>
        
        <!-- Breakdown Section (Hidden by default) -->
        <div id="${breakdownId}" class="breakdown-content hidden border-t border-slate-200 bg-slate-50 px-4 py-3">
            <div class="space-y-2 text-sm">
                ${createRow('Base Freight', (breakdown.base_freight || 0) + (breakdown.profit_margin || 0))}
                ${createRow('EDL Charge', breakdown.edl_charge)}
                ${createRow('Docket Fee', breakdown.docket_fee)}
                ${createRow('Eway Bill Fee', breakdown.eway_bill_fee)}
                ${createRow('Fuel Surcharge', breakdown.fuel_surcharge)}
                ${createRow('Hamali Charge', breakdown.hamali_charge)}
                ${createRow('Pickup Charge', breakdown.pickup_charge)}
                ${createRow('Delivery Charge', breakdown.delivery_charge)}
                ${createRow('FOD Charge', breakdown.fod_charge)}
                ${createRow('DOD Charge', breakdown.dod_charge)}
                ${createRow('Risk Charge', breakdown.risk_charge)}
                ${createRow('FOV Charge', breakdown.fov_charge)}
                ${createRow('ECC Charge', breakdown.ecc_charge)}
                ${createRow('COD Charge', breakdown.cod_charge)}
                <div class="flex justify-between items-center pt-2 border-t border-slate-300">
                    <span class="text-slate-600">GST (18%):</span>
                    <span class="font-semibold text-slate-800">₹${(breakdown.gst_amount || 0).toFixed(2)}</span>
                </div>
                <div class="flex justify-between items-center pt-2 border-t-2 border-brand-blue">
                    <span class="font-bold text-slate-800">Total:</span>
                    <span class="font-bold text-brand-blue text-lg">₹${rate.total_cost.toFixed(2)}</span>
                </div>
            </div>
        </div>
    </div>
`;
    }).join('');

    container.innerHTML = html;
}

// Toggle breakdown visibility
function toggleBreakdown(breakdownId) {
    const breakdownEl = document.getElementById(breakdownId);
    const iconEl = document.getElementById(`${breakdownId}-icon`);

    if (breakdownEl && iconEl) {
        breakdownEl.classList.toggle('hidden');
        iconEl.classList.toggle('rotate-180');
    }
}

// ============================================================================
// FTL Calculator Logic
// ============================================================================

function updateCalcFTLDestinations() {
    const sourceCity = document.getElementById('calc-ftl-source').value;
    const destSelect = document.getElementById('calc-ftl-dest');
    const containerSelect = document.getElementById('calc-ftl-container');

    destSelect.innerHTML = '<option value="">Select Destination</option>';
    containerSelect.innerHTML = '<option value="">Select Container</option>';

    if (sourceCity && ftlRatesData[sourceCity]) {
        const destinations = ftlRatesData[sourceCity];
        Object.keys(destinations).forEach(dest => {
            const option = document.createElement('option');
            option.value = dest;
            option.textContent = dest;
            destSelect.appendChild(option);
        });
    }
    document.getElementById('calc-ftl-results').classList.add('hidden');
}

function updateCalcFTLContainerTypes() {
    const sourceCity = document.getElementById('calc-ftl-source').value;
    const destCity = document.getElementById('calc-ftl-dest').value;
    const containerSelect = document.getElementById('calc-ftl-container');

    containerSelect.innerHTML = '<option value="">Select Container</option>';

    if (sourceCity && destCity && ftlRatesData[sourceCity] && ftlRatesData[sourceCity][destCity]) {
        const containerTypes = ftlRatesData[sourceCity][destCity];
        containerTypes.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            containerSelect.appendChild(option);
        });
    }
    document.getElementById('calc-ftl-results').classList.add('hidden');
}

// Populate Source on Load (triggered by showSection)
function initFTLCalcDropdowns() {
    const sourceSelect = document.getElementById('calc-ftl-source');
    if (!sourceSelect) return;

    if (sourceSelect.options.length <= 1 && Object.keys(ftlRatesData).length > 0) {
        Object.keys(ftlRatesData).forEach(city => {
            const option = document.createElement('option');
            option.value = city;
            option.textContent = city;
            sourceSelect.appendChild(option);
        });
    }
}

async function calculateFTLRateSubmit(e) {
    e.preventDefault();
    const source = document.getElementById('calc-ftl-source').value;
    const dest = document.getElementById('calc-ftl-dest').value;
    const type = document.getElementById('calc-ftl-container').value;
    const resultsContainer = document.getElementById('calc-ftl-results');

    try {
        // Show loading state (manual since FTL has no specific list container)
        const submitBtn = e.target.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Calculating...';
        submitBtn.disabled = true;

        resultsContainer.classList.add('hidden');

        const response = await fetch(`${API_BASE}/api/ftl/calculate-rate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                source_city: source,
                destination_city: dest,
                container_type: type
            })
        });

        if (response.ok) {
            const data = await response.json();
            resultsContainer.classList.remove('hidden');

            // User Request: Base Price = Base + Escalation
            document.getElementById('calc-ftl-base').textContent = '₹' + data.price_with_escalation.toFixed(2);
            document.getElementById('calc-ftl-gst').textContent = '₹' + data.gst_amount.toFixed(2);
            document.getElementById('calc-ftl-total').textContent = '₹' + data.total_price.toFixed(2);
        } else {
            const error = await response.json();
            const errorMsg = error.detail || 'Calculation failed';

            if (window.toast) toast.error(errorMsg);
            console.warn(`FTL Calculation Failed: ${response.status}`, error);
        }
    } catch (err) {
        console.error(err);
        const isNetworkError = err.name === 'TypeError' && err.message === 'Failed to fetch';
        const msg = isNetworkError ? "Network Error: Unable to connect" : "Failed to calculate FTL rate";

        if (window.toast) toast.error(msg);
    } finally {
        // Reset button
        const submitBtn = e.target.querySelector('button[type="submit"]');
        submitBtn.textContent = 'Calculate FTL Rate';
        submitBtn.disabled = false;
    }
}
