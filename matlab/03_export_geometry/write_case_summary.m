function write_case_summary(summaryFile, cases)
%WRITE_CASE_SUMMARY Write a simple summary table from a struct array.
T = struct2table(cases);
writetable(T, summaryFile);
end
