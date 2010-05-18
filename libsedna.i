%module libsedna
%{
#include "libsedna.h"
int SEsetConnectionAttrInt(struct SednaConnection * conn, enum SEattr attr, int value)
{
        return SEsetConnectionAttr(conn,attr,&value,sizeof(int));
}
int SEsetConnectionAttrStr(struct SednaConnection * conn, enum SEattr attr, char * value)
{
        return SEsetConnectionAttr(conn,attr,value,strlen(value));
}
%}
/* Note that this is not smart because we introduce some private stuff this way. */ 
%include "libsedna.h"
int SEsetConnectionAttrInt(struct SednaConnection *,enum SEattr,int);
int SEsetConnectionAttrStr(struct SednaConnection *,enum SEattr,char *);

