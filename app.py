from flask import Flask, render_template, request, redirect, url_for
import json
import nbformat
from nbclient import NotebookClient

app = Flask(__name__)

# Route for the form
@app.route('/')
def form():
    try:
        with open('inputs.json') as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        data = None  # No data yet
    return render_template('form.html', data=data)

# Route to handle form submission and save to JSON
@app.route('/submit', methods=['POST'])
def submit_form():
    # Retrieve form data
    warehousesNbre = int(request.form['warehouses'])
    customersNbre = int(request.form['customers'])

    # Fixed costs
    fixed_costs = [int(request.form[f'fixed_cost_{i}']) for i in range(warehousesNbre)]
    
    # Transportation costs
    transport_costs = []
    for i in range(warehousesNbre):
        row = [int(request.form[f'transport_cost_{i}_{j}']) for j in range(customersNbre)]
        transport_costs.append(row)
    # Variable costs
    variable_costs = [int(request.form[f'variable_cost_{i}']) for i in range(warehousesNbre)]
    # penalty costs
    penality_costs = [int(request.form[f'penality_cost_{i}']) for i in range(customersNbre)]
    # demands
    demands = [int(request.form[f'demand_{i}']) for i in range(customersNbre)]
    # Capacities
    capacities = [int(request.form[f'capacity_{i}']) for i in range(warehousesNbre)]
    # Min service time
    min_service = [float(request.form[f'min_service_{i}']) for i in range(customersNbre)] 
   
    # Construct the data dictionary
    data = {
        "warehousesNbre": warehousesNbre,
        "customersNbre": customersNbre,
        "fixed_costs": fixed_costs,
        "transport_costs": transport_costs,
        "variable_costs": variable_costs,
        "penality_costs": penality_costs,
        "demands": demands,
        "capacities": capacities,
        "min_service": min_service,
    }

    print(request.form)  # Debugging step to inspect the submitted data

    # Save the data to a JSON file
    with open('inputs.json', 'w') as json_file:
        json.dump(data, json_file, indent=4)

    # Redirect back to the homepage
    #return redirect(url_for('form'))
    return render_template('form.html')

# Route to run the Jupyter notebook
@app.route('/run_notebook', methods=['POST'])
def run_notebook():
    try:
        # Load the notebook
        with open('main.ipynb') as f:
            nb = nbformat.read(f, as_version=4)
        
        # Create a client for executing the notebook
        client = NotebookClient(nb)
        
        # Execute the notebook
        client.execute()

        # Get the output of the last cell
        last_cell = nb['cells'][-1]  # Get the last cell
        details_cell = nb['cells'][-2] # Get the details cell
        # Initialize outputs
        details_output = "No details found."
        text_output = "No output found."
        # Extract details from the second-to-last cell
        if 'outputs' in details_cell:
            details_output = ""
            for out in details_cell['outputs']:
                if out.output_type == 'stream':
                    details_output += out.text
                elif out.output_type == 'execute_result':
                    details_output += out['data'].get('text/plain', '')

        # Extract output from the last cell
        if 'outputs' in last_cell:
            text_output = ""
            for out in last_cell['outputs']:
                if out.output_type == 'stream':
                    text_output += out.text
                elif out.output_type == 'execute_result':
                    text_output += out['data'].get('text/plain', '')

        # Pass both outputs to the template
        return render_template('form.html', details=details_output, output=text_output)

    except Exception as e:
        return render_template('form.html', details="Error", output=f"Error running notebook: {e}")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'json_file' not in request.files:
        return "No file part", 400

    file = request.files['json_file']
    if file.filename == '':
        return "No selected file", 400

    if file and file.filename.endswith('.json'):
        # Read the file and parse JSON content
        try:
            data = json.load(file)

            # Save the data into the inputs.json file, overwriting the existing file
            with open('inputs.json', 'w') as f:
                json.dump(data, f, indent=4)

            # Optionally return the parsed JSON data for confirmation
            return render_template('form.html',)
        except json.JSONDecodeError:
            return render_template('form.html', output=json.JSONDecodeError)
    else:
        return render_template('form.html', output="Invalid file type. Only .json files are allowed.")

if __name__ == '__main__':
    app.run(debug=True)
