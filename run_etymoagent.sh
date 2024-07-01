#!/bin/bash
export ETYMOAGENT=/Users/nazlidenizurenli/ndu_code/EtymoAgent
/opt/anaconda3/envs/etymoagent/bin/python3 scripts/main.py

# Step 1: Set up the database 
# echo "Step 1: Setting up the database..."
# python3 scripts/db_setup.py

# # Step 2: Run data scraping script
# echo "Step 2: Running data scraper..."
# python3 scripts/data_scraper.py

# # Step 3: Train machine learning models
# echo "Step 3: Training machine learning models..."
# python3 scripts/train_model.py

# # Step 4: Run the API
# echo "Step 4: Running the API..."
# python3 api/app.py &

# # Step 5: Run the web application
# echo "Step 5: Running the web application..."
# python3 web/app.py &

# # Wait for services to start
# sleep 5

# # Step 6: Perform API call or interact with the application
# echo "Step 6: Performing API call or interacting with the application..."
# # Example: curl or API call here

# # Step 7: Stop services (optional)
# # echo "Step 7: Stopping services..."
# # ps aux | grep 'python3 app.py' | grep -v grep | awk '{print $2}' | xargs kill

# # Step 8: Clean up (optional)
# # echo "Step 8: Cleaning up..."
# # rm -rf EtymoAgent

# # Step 9: Return result
# echo "EtymoAgent process completed successfully!"
