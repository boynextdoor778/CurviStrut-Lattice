function export_centerline_to_json(caseData, jsonFile)
%EXPORT_CENTERLINE_TO_JSON Export repeated centerline data to Abaqus-readable JSON.

if ~isfield(caseData, 'strutPaths')
    error('caseData must contain strutPaths.');
end
if ~isfield(caseData, 'cellSizeMM')
    caseData.cellSizeMM = 20.0;
end
if ~isfield(caseData, 'radiusMM')
    caseData.radiusMM = caseData.radiusNorm * caseData.cellSizeMM;
end
if ~isfield(caseData, 'caseName')
    caseData.caseName = 'unnamed_case';
end

J = struct();
J.case_name = caseData.caseName;
if isfield(caseData, 'branchName'); J.branch_name = caseData.branchName; else; J.branch_name = ''; end
J.cell_size_mm = caseData.cellSizeMM;
J.radius_mm = caseData.radiusMM;
J.radius_norm = caseData.radiusNorm;
J.bend_amp = caseData.bendAmp;
J.nPtsPerArm = caseData.nPtsPerArm;
J.refAxis = caseData.refAxis;
if isfield(caseData, 'repeatN'); J.repeatN = caseData.repeatN; else; J.repeatN = [1 1 1]; end
if isfield(caseData, 'H0_mm'); J.H0_mm = caseData.H0_mm; else; J.H0_mm = max(J.repeatN) * J.cell_size_mm; end
if isfield(caseData, 'A0_mm2'); J.A0_mm2 = caseData.A0_mm2; else; J.A0_mm2 = 1.0; end

struts = struct('id', {}, 'points', {});
for k = 1:numel(caseData.strutPaths)
    P_norm = caseData.strutPaths{k};
    P_mm = P_norm * caseData.cellSizeMM;
    struts(k).id = k; %#ok<AGROW>
    struts(k).points = P_mm; %#ok<AGROW>
end
J.struts = struts;

jsonText = jsonencode(J, 'PrettyPrint', true);
fid = fopen(jsonFile, 'w');
if fid == -1
    error('Cannot open JSON file for writing: %s', jsonFile);
end
cleanupObj = onCleanup(@() fclose(fid)); %#ok<NASGU>
fwrite(fid, jsonText, 'char');
end
