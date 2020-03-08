# BmsDatUtils

This is an unofficial library to read, write BMS dat files.

Features v0.1:
   * Read, write BASIC AERODYNAMIC COEFFICIENTS section
   * Add new mach breakpoints(cl, cd, cy values are inter/extrapolated for the newly created mach breakpoint)

Note: This library was hastly hacked together to change the drag values for an addon aircraft, feel free to improve upon it.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

Python 3

### Installing

Copy bms folder into your project.

Example:
```
import matplotlib.pyplot as plt
from bms import BasicFlightModel as FM


def plot_mach(x_axis, values, alpha_index=0):
    y_coords = []
    for i in range(0, len(x_axis)):
        value = values[i][alpha_index]
        y_coords.append(value)

    plt.plot(x_axis, y_coords, label=str(alpha_index))

def main():
    fm = FM.load_dat("f16bk52.dat")

    plot_mach(fm.mach_breakpoints, fm.cd, 8)
    plt.show()

    FM.save_dat(fm , "f16bk52_new.dat")
```

## Running the tests

N/A for now

## Contributing

If you want to contribute create or claim a ticket then create a pull request.

## Authors

* **Adam Doda** - *Initial work* - [adamdoda](https://github.com/adamdoda)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
