import matplotlib
matplotlib.use('TkAgg')  # Use TkAgg backend for better interactivity

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import textwrap
import argparse
from matplotlib.dates import date2num, num2date, MonthLocator, DateFormatter

plt.ion()  # Enable interactive mode

def read_data(filename):
    """Optimized CSV reading with modern date parsing"""
    try:
        df = pd.read_csv(
            filename, 
            skiprows=1,
            names=['Resource', 'Project', 'Start', 'End'],
            dtype={'Start': 'object', 'End': 'object'}
        )
        df['Start'] = pd.to_datetime(df['Start'], format='mixed')
        df['End'] = pd.to_datetime(df['End'], format='mixed')
        return df.dropna()
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return pd.DataFrame()

def generate_colors(num_projects):
    """Efficient color generation with caching"""
    colormap = plt.colormaps['tab20']
    return colormap(np.linspace(0, 1, num_projects))

def wrap_text(text, width=20):
    """Optimized text wrapping with cache"""
    return textwrap.fill(text, width=width)

def create_gantt_chart(df, text_width):
    """Optimized chart creation with toggle details functionality"""
    if df.empty:
        print("No valid data to create chart.")
        return

    # Precompute values
    projects = df['Project'].unique()
    colors = generate_colors(len(projects))
    color_map = dict(zip(projects, colors))
    
    df['Start_num'] = date2num(df['Start'])
    df['End_num'] = date2num(df['End'])
    df['Duration'] = df['End_num'] - df['Start_num']

    fig, ax = plt.subplots(figsize=(16, 10))
    
    # Plot bars with proper indexing
    bars = ax.barh(
        y=np.arange(len(df)),
        width=df['Duration'],
        left=df['Start_num'],
        height=0.6,
        color=[color_map[p] for p in df['Project']],
        alpha=0.8
    )

    # Add labels using vectorized operations
    bar_labels = []
    original_texts = []
    for idx, bar in enumerate(bars):
        original_text = wrap_text(df.iloc[idx]['Project'], 15)
        label = ax.text(
            bar.get_x() + bar.get_width()/2,
            bar.get_y() + bar.get_height()/2,
            original_text,
            ha='center', va='center',
            color='white', fontsize=8, fontweight='bold'
        )
        bar_labels.append(label)
        original_texts.append(original_text)

    # Configure axes
    ax.set_yticks(np.arange(len(df)))
    ax.set_yticklabels([wrap_text(r, text_width) for r in df['Resource']])
    ax.invert_yaxis()
    
    # Date formatting and grid
    min_date = df['Start'].min()
    max_date = df['End'].max()
    ax.set_xlim(date2num(min_date), date2num(max_date))
    
    # Set major ticks to months and minor ticks to weeks
    ax.xaxis.set_major_locator(MonthLocator())
    ax.xaxis.set_major_formatter(DateFormatter('%b %Y'))
    
    # Add grid for months
    ax.grid(True, axis='x', which='major', linestyle='--', color='gray', alpha=0.5)
    
    # Rotate and align the tick labels so they look better
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

    # Legend handling
    handles = [plt.Rectangle((0,0),1,1, color=color) for color in color_map.values()]
    ax.legend(handles, [wrap_text(p, 15) for p in color_map], 
             title="Projects", loc="center left", bbox_to_anchor=(1, 0.5))

    # Track which bar is currently showing details
    active_bar = None

    def on_click(event):
        nonlocal active_bar
        if event.inaxes == ax:
            for i, bar in enumerate(bars):
                if bar.contains(event)[0]:
                    # If clicking the same bar again, reset it
                    if active_bar == i:
                        bar_labels[i].set_text(original_texts[i])
                        bar_labels[i].set_color('white')
                        bar_labels[i].set_fontsize(8)
                        active_bar = None
                    else:
                        # Reset previously active bar
                        if active_bar is not None:
                            bar_labels[active_bar].set_text(original_texts[active_bar])
                            bar_labels[active_bar].set_color('white')
                            bar_labels[active_bar].set_fontsize(8)

                        # Show details for all resources of the same project
                        project = df.iloc[i]['Project']
                        project_resources = df[df['Project'] == project]
                        
                        info = f"Project: {project}\n"
                        for _, resource in project_resources.iterrows():
                            info += (f"Resource: {resource['Resource']}\n"
                                     f"Start: {resource['Start'].strftime('%b %Y')}\n"
                                     f"End: {resource['End'].strftime('%b %Y')}\n"
                                     f"Duration: {(resource['End'] - resource['Start']).days} days\n\n")
                        
                        bar_labels[i].set_text(info.strip())
                        bar_labels[i].set_color('red')
                        bar_labels[i].set_fontsize(10)
                        active_bar = i
                    
                    fig.canvas.draw_idle()
                    break

    fig.canvas.mpl_connect('button_press_event', on_click)
    
    plt.tight_layout()
    plt.show(block=True)  # This will keep the window open

def main():
    parser = argparse.ArgumentParser(description="Generate optimized Gantt chart")
    parser.add_argument("file", type=str, help="CSV file path")
    parser.add_argument("--text_width", type=int, default=30, 
                       help="Text wrap width (default: 30)")
    args = parser.parse_args()

    df = read_data(args.file)
    if not df.empty:
        create_gantt_chart(df, args.text_width)

if __name__ == "__main__":
    main()
plt.show(block=True)