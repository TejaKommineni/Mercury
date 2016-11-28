set terminal png
set output "message-rtt.png"
set style data boxplot
set style boxplot outliers pointtype 7
set style fill solid 0.25 border lt -1
set boxwidth 0.2
set pointsize 0.75
unset key
set logscale y
set border 2
set xlabel "Message Rate (messages/second)"
set ylabel "RTT (seconds)"
set xtics ("1" 1, "10" 2, "100" 3, "250" 4, "500" 5, "750" 6, "1000" 7) scale 0.0
plot 'run-baseline' using (1):3, 'run-10' using (2):3, 'run-100' using (3):3, 'run-250' using (4):3, 'run-500' using (5):3, 'run-750' using (6):3, 'run-1000' using (7):3
#pause -1 "Hit any key to continue"
