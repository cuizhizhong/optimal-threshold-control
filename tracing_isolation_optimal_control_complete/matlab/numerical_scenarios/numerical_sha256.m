function value = numerical_sha256(input,kind)
% SHA-256；结构体字段排序后序列化，文件按原始字节计算。
if nargin<2, kind='value'; end
md=java.security.MessageDigest.getInstance('SHA-256');
if strcmp(kind,'file')
    fid=fopen(input,'rb'); assert(fid>=0,'Cannot open hash input: %s',input);
    cleanup=onCleanup(@() fclose(fid));
    while ~feof(fid)
        bytes=fread(fid,1024*1024,'*uint8'); md.update(typecast(bytes,'int8'));
    end
else
    bytes=unicode2native(jsonencode(canonical(input)),'UTF-8');
    md.update(typecast(uint8(bytes),'int8'));
end
bytes=typecast(md.digest(),'uint8');
value=lower(reshape(dec2hex(bytes,2)',1,[]));
end

function value=canonical(value)
if isstruct(value)
    value=orderfields(value);
    fields=fieldnames(value);
    for k=1:numel(value)
        for j=1:numel(fields), value(k).(fields{j})=canonical(value(k).(fields{j})); end
    end
elseif iscell(value)
    for k=1:numel(value), value{k}=canonical(value{k}); end
end
end
