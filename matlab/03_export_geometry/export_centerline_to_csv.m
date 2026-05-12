function export_centerline_to_csv(caseData, csvFile)
%EXPORT_CENTERLINE_TO_CSV Export path points to a flat CSV table.
rows = [];
for k = 1:numel(caseData.strutPaths)
    P = caseData.strutPaths{k};
    for i = 1:size(P,1)
        rows = [rows; k, i, P(i,:)]; %#ok<AGROW>
    end
end
T = array2table(rows, 'VariableNames', {'StrutID','PointID','X','Y','Z'});
writetable(T, csvFile);
end
