import os
import math
import random
import numpy as np
import scipy.special

def generate_isotropic_laplace_noise_offset(epsilon):
    theta = np.random.uniform(0, 2 * math.pi)  # Pick a random angle in [0, 2*pi) (theta)
    p = random.random()  # Generate a uniform random probability in [0, 1) (p)
    # Calculate noise distance using the Lambert W function for Laplace noise transformation
    # Source: https://github.com/quao627/GeoPrivacy/blob/main/GeoPrivacy/mechanism.py
    r = -1 / epsilon * (scipy.special.lambertw((p - 1) / math.e, k=-1, tol=1e-8).real + 1)  # (r)
    return r, theta  # Return the computed noise offset as (r, theta)

def add_privacy_noise_to_geographic_coordinate(longitude, latitude, epsilon):
    noise_distance_m, noise_angle = generate_isotropic_laplace_noise_offset(epsilon)  # Generate noise parameters
    noise_lat_deg = (noise_distance_m * math.sin(noise_angle)) / 111320  # Convert noise distance to degrees latitude
    noise_lon_deg = (noise_distance_m * math.cos(noise_angle)) / (111320 * math.cos(math.radians(latitude)))  # Convert noise distance to degrees longitude (adjusted by latitude)
    return longitude + noise_lon_deg, latitude + noise_lat_deg  # Return the new geographic coordinates with added noise

def read_geographic_coordinates(file_path):
    with open(file_path, "r") as file:  # Open file for reading
        lines = file.read().strip().splitlines()  # Read all lines and remove extraneous whitespace
    coordinates = []  # Initialize list to store coordinate tuples
    for line in lines:  # Process each line of the file
        parts = line.split(",")  # Split the line by comma
        # Check if there are exactly 2 parts and both are non-empty after stripping whitespace
        if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
            print(f"Warning: Skipping malformed line in {file_path}: {line}")  # Warn and skip malformed line
            continue
        try:
            lon, lat = float(parts[0].strip()), float(parts[1].strip())  # Convert strings to floats
            # Check if longitude and latitude are within valid geographic ranges
            if lon < -180 or lon > 180 or lat < -90 or lat > 90:
                print(f"Warning: Skipping out-of-range coordinate in {file_path}: {line}")  # Warn and skip if coordinate is out of range
                continue
            coordinates.append((lon, lat))  # Append valid coordinate tuple to the list
        except ValueError:
            print(f"Warning: Skipping malformed line in {file_path}: {line}")  # Warn and skip if conversion fails
    return coordinates  # Return the list of geographic coordinates

def write_geographic_coordinates(coordinates, file_path):
    with open(file_path, "w") as file:  # Open file for writing
        file.write("Longitude,Latitude\n")  # Write CSV header for perturbed coordinates only
        for longitude, latitude in coordinates:  # Iterate over each coordinate tuple
            file.write(f"{longitude},{latitude}\n")  # Write coordinate data as a CSV row

def write_geographic_coordinates_with_original(original_coords, perturbed_coords, file_path):
    with open(file_path, "w") as file:  # Open file for writing
        file.write("Latitude,Longitude,Perturbed Latitude,Perturbed Longitude\n")  # Write CSV header with original and perturbed coordinates
        for (orig_lon, orig_lat), (pert_lon, pert_lat) in zip(original_coords, perturbed_coords):  # Iterate over paired original and perturbed coordinates
            # Swap original coordinate order to (Latitude, Longitude) and perturbed coordinate order similarly
            file.write(f"{orig_lat},{orig_lon},{pert_lat},{pert_lon}\n")  # Write the row with both sets of coordinates

def process_privacy_dataset(input_directory, output_directory, epsilon, include_original=False):
    if not os.path.exists(output_directory):  # Check if the output directory exists
        os.makedirs(output_directory)  # Create the output directory if it doesn't exist
    for file_name in os.listdir(input_directory):  # Loop through each file in the input directory
        input_file_path = os.path.join(input_directory, file_name)  # Construct full file path
        if not os.path.isfile(input_file_path):  # Skip directories or non-file items
            continue
        coordinates = read_geographic_coordinates(input_file_path)  # Read coordinates from the file
        perturbed_coordinates = []  # List to collect coordinates with added noise
        for longitude, latitude in coordinates:  # Apply noise to each coordinate
            perturbed_coordinates.append(add_privacy_noise_to_geographic_coordinate(longitude, latitude, epsilon))
        base_name, ext = os.path.splitext(file_name)  # Separate the file name and its extension
        output_file_name = f"{base_name}_eps{epsilon}{ext}"  # Create a new filename indicating the applied epsilon
        output_file_path = os.path.join(output_directory, output_file_name)  # Construct the output file path
        if include_original:
            write_geographic_coordinates_with_original(coordinates, perturbed_coordinates, output_file_path)  # Save both original and perturbed coordinates to file
        else:
            write_geographic_coordinates(perturbed_coordinates, output_file_path)  # Save only the perturbed coordinates to file
        print(f"Processed {file_name} -> {output_file_name}")  # Log the successful processing of the file

def main():
    epsilon = 0.01  # Define the privacy parameter epsilon
    input_directory = "./data"  # Define the input directory path
    output_directory = "./noisy_data"  # Define the output directory path
    include_original = True  # Toggle: set to True to include original coordinates; set to False for perturbed only
    process_privacy_dataset(input_directory, output_directory, epsilon, include_original)

if __name__ == "__main__":
    main()
